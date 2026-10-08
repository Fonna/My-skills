#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出 Chrome 阅读清单（Reading List）。

数据在 User Data/<Profile>/Sync Data/LevelDB 里，键名 reading_list-dt-<url>，
值为 protobuf：f1=规范URL, f2=标题, f3=显示URL, f4=添加时间(Unix微秒),
f5=更新时间, f6=已读标记(0/1)。纯只读，Chrome 运行中也可以直接导出。
"""
import argparse
import datetime
import glob
import json
import os
import re
import struct
import subprocess
import sys

LOG_BLOCK = 32768
CRAM = None  # lazy-loaded cramjam module


def ensure_cramjam():
    global CRAM
    if CRAM is None:
        try:
            import cramjam
        except ImportError:
            print('[setup] 安装 cramjam（snappy 解压依赖）...', file=sys.stderr)
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'cramjam'])
            import cramjam
        CRAM = cramjam
    return CRAM


def get_varint(buf, pos):
    result = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7


def decompress(data, ctype):
    if ctype == 0:
        return data
    if ctype == 1:
        # .ldb 块是 raw Snappy 格式，不是 framed，必须用 decompress_raw
        return bytes(CRAM.snappy.decompress_raw(data))
    if ctype == 2:
        return bytes(CRAM.zstd.decompress(data))
    raise ValueError('unknown block compression %d' % ctype)


def parse_block_entries(data):
    """遍历块内条目，须在末尾 restart 数组前停止。

    块结构: [条目...][restart 数组][num_restarts(4)]，条目为
    shared_len varint + non_shared_len varint + value_len varint + key_delta + value。
    """
    if len(data) < 4:
        return []
    num_restarts = struct.unpack('<I', data[-4:])[0]
    limit = len(data) - 4 - num_restarts * 4
    if limit <= 0:
        return []
    pos = 0
    key = b''
    out = []
    while pos < limit:
        try:
            shared, pos = get_varint(data, pos)
            non_shared, pos = get_varint(data, pos)
            vlen, pos = get_varint(data, pos)
        except IndexError:
            break
        if pos + non_shared + vlen > limit:
            break
        key = key[:shared] + data[pos:pos + non_shared]
        pos += non_shared
        val = data[pos:pos + vlen]
        pos += vlen
        out.append((key, val))
    return out


def parse_block_with_trailer(raw):
    # BlockHandle.size 不含块尾 5 字节，raw = 块体 + [crc(4)][type(1)]
    ctype = raw[-5]
    data = decompress(raw[:-5], ctype)
    return parse_block_entries(data)


def read_ldb(path):
    """SSTable (.ldb)：yield (user_key, seq, record_type, value)。"""
    raw = open(path, 'rb').read()
    footer = raw[-48:]
    if footer[-8:] != b'\x57\xfb\x80\x8b\x24\x75\x47\xdb':
        return
    pos = 0
    m_off, pos = get_varint(footer, pos)
    m_size, pos = get_varint(footer, pos)
    i_off, pos = get_varint(footer, pos)
    i_size, pos = get_varint(footer, pos)
    idx_block = parse_block_with_trailer(raw[i_off:i_off + i_size + 5])
    for _ikey, handle in idx_block:
        b_off, hp = get_varint(handle, 0)
        b_size, hp = get_varint(handle, hp)
        block = parse_block_with_trailer(raw[b_off:b_off + b_size + 5])
        for key, val in block:
            if len(key) < 8:
                continue
            trailer = struct.unpack('<Q', key[-8:])[0]
            yield key[:-8], trailer >> 8, trailer & 0xFF, val


def read_log(path):
    """WAL (.log)：32KB 块 + 7 字节记录头，写批次内为内键记录。"""
    data = open(path, 'rb').read()
    pos = 0
    rec = b''
    while pos + 7 <= len(data):
        block_off = pos % LOG_BLOCK
        if LOG_BLOCK - block_off < 7:
            pos += LOG_BLOCK - block_off
            continue
        _crc, length, ltype = struct.unpack('<IHB', data[pos:pos + 7])
        payload = data[pos + 7:pos + 7 + length]
        pos += 7 + length
        if ltype == 0:  # 块尾填充
            rec = b''
            continue
        rec = rec + payload
        if ltype in (1, 4):  # full / last 分片，凑齐一个写批次
            batch, rec = rec, b''
            if len(batch) < 12:
                continue
            count = struct.unpack('<I', batch[8:12])[0]
            bp = 12
            for _ in range(count):
                try:
                    rtype = batch[bp]
                    bp += 1
                    klen, bp = get_varint(batch, bp)
                    key = batch[bp:bp + klen]
                    bp += klen
                    vlen, bp = get_varint(batch, bp)
                    val = batch[bp:bp + vlen]
                    bp += vlen
                except (IndexError, struct.error):
                    break
                if len(key) >= 8:
                    trailer = struct.unpack('<Q', key[-8:])[0]
                    yield key[:-8], trailer >> 8, trailer & 0xFF, val


def proto_fields(buf):
    """顶层 protobuf 字段 {字段号: 值}。重复字段号也必须推进 pos，否则整体错位。"""
    fields = {}
    pos = 0
    while pos < len(buf):
        try:
            tag, pos = get_varint(buf, pos)
            fnum, wt = tag >> 3, tag & 7
            if wt == 0:
                v, pos = get_varint(buf, pos)
            elif wt == 2:
                ln, pos = get_varint(buf, pos)
                v = buf[pos:pos + ln]
                pos += ln
            elif wt == 5:
                v = None
                pos += 4
            elif wt == 1:
                v = None
                pos += 8
            else:
                break
            if fnum not in fields:
                fields[fnum] = v
        except IndexError:
            break
    return fields


def fmt_us(us):
    try:
        return datetime.datetime.fromtimestamp(us / 1e6).strftime('%Y-%m-%d %H:%M')
    except (ValueError, OSError, OverflowError):
        return '?'


def collect(leveldb_dir):
    ensure_cramjam()
    records = {}
    files = sorted(glob.glob(os.path.join(leveldb_dir, '*.ldb'))) + \
        sorted(glob.glob(os.path.join(leveldb_dir, '*.log')))
    for f in files:
        it = read_ldb(f) if f.endswith('.ldb') else read_log(f)
        for uk, seq, rtype, val in it:
            # kTypeValue == 1（0 是删除墓碑）；同一 key 取最新 seq
            if rtype == 1 and val and b'reading_list-dt-' in uk:
                cur = records.get(uk)
                if cur is None or seq > cur[0]:
                    records[uk] = (seq, val)
    by_url = {}
    for uk, (seq, val) in records.items():
        m = re.match(rb'reading_list-dt-(.+)', uk)
        if not m:
            continue
        key_url = m.group(1).decode('utf-8', 'replace')
        fs = proto_fields(val)

        def gs(i):
            v = fs.get(i, b'')
            return v.decode('utf-8', 'replace') if isinstance(v, bytes) else ''

        entry = {
            'title': gs(2) or key_url,
            'url': gs(3) or gs(1) or key_url,
            'added': fs.get(4, 0),
            'updated': fs.get(5, 0),
            'read': bool(fs.get(6, 0)),
            'seq': seq,
        }
        cur = by_url.get(key_url)
        if cur is None or seq > cur['seq']:
            by_url[key_url] = entry
    return sorted(by_url.values(), key=lambda e: (e['added'], e['seq']), reverse=True)


def write_markdown(entries, out_path):
    read_n = sum(1 for e in entries if e['read'])
    lines = [
        '# Chrome 阅读清单（Reading List）导出', '',
        '共 %d 条（未读 %d / 已读 %d），导出于 %s。' % (
            len(entries), len(entries) - read_n, read_n,
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M')), '',
        '| # | 状态 | 添加时间 | 标题 | URL |',
        '|---|---|---|------|-----|',
    ]
    for i, e in enumerate(entries, 1):
        title = e['title'].replace('|', '\\|').replace('\n', ' ')
        st = '已读' if e['read'] else '**未读**'
        lines.append('| %d | %s | %s | %s | %s |' % (
            i, st, fmt_us(e['added']), title[:90], e['url']))
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def resolve_leveldb(user_data, profile):
    d = os.path.join(user_data, profile, 'Sync Data', 'LevelDB')
    if os.path.isdir(d):
        return d
    print('[!] %s 下没有 Sync Data/LevelDB' % os.path.join(user_data, profile), file=sys.stderr)
    for name in sorted(os.listdir(user_data)):
        if os.path.isdir(os.path.join(user_data, name, 'Sync Data', 'LevelDB')):
            print('    可用 Profile: %s' % name, file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description='导出 Chrome 阅读清单为 Markdown/JSON')
    ap.add_argument('--out', default='chrome_reading_list.md', help='Markdown 输出路径')
    ap.add_argument('--json', help='可选：同时输出 JSON（含全部字段）')
    ap.add_argument('--profile', default='Default', help='Chrome Profile 名（默认 Default）')
    ap.add_argument('--user-data',
                    default=os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data'),
                    help='Chrome User Data 目录')
    args = ap.parse_args()

    leveldb = resolve_leveldb(args.user_data, args.profile)
    entries = collect(leveldb)
    if not entries:
        print('[!] 未解析到任何条目。先用二进制 grep 确认数据存在：', file=sys.stderr)
        print('    grep -a -c "reading_list-dt-" "%s"/*.ldb' % leveldb, file=sys.stderr)
        sys.exit(2)

    write_markdown(entries, args.out)
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=1)

    read_n = sum(1 for e in entries if e['read'])
    print('共 %d 条（未读 %d / 已读 %d）' % (len(entries), len(entries) - read_n, read_n))
    print('时间范围: %s -> %s' % (fmt_us(entries[-1]['added']), fmt_us(entries[0]['added'])))
    print('输出: %s%s' % (args.out, ' + ' + args.json if args.json else ''))
    for e in entries[:10]:
        print('  %s | %s | %s' % (fmt_us(e['added']), '读' if e['read'] else '未', e['title'][:40]))


if __name__ == '__main__':
    main()
