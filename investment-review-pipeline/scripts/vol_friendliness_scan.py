# -*- coding: utf-8 -*-
"""波动友好度扫描：全品种 ATR% / 日内振幅% / 搓揉率 / 反转率 → 友好度排名。

用途：作为常做品种筛选标配——波动越干净（幅度小、反转/搓揉少）的品种越好做，
      排名靠前的优先纳入主攻清单，排名靠后（高波动+高反转）需压仓或机械单。

用法：
  python vol_friendliness_scan.py [--data-dir data] [--today YYYY-MM-DD] [--window 60] [--md]

输出：
  终端打印排名表；--md 同时打印 markdown 表（便于贴知识库）。

指标定义（与复盘 §十 口径一致）：
  - ATR%    = 近 window 日平均真实波幅 / 最新收盘 ×100（波动幅度，含跳空）
  - 日内振幅% = 近 window 日 (H-L)/C 均值（实体振幅）
  - 搓揉率%  = 近 window 日 实体占比<0.35 的 K 线比例（多空拉锯十字）
  - 反转率%  = 近 window 日 收阳却收在下部(上影长)/收阴却收在上部(下影长) 的比例（假突破洗盘）
  - 友好度   = 100 - (ATR%归一 + 日内幅%归一 + 反转率%归一)/3（组内相对分，随参与品种变化）
"""
import csv, os, glob, argparse, statistics


# 交易所标准品种代码 → 中文名（依据各交易所上市合约代码，非编造）
NAMES = {
    "AL": "沪铝", "AO": "氧化铝", "C": "玉米", "FG": "玻璃", "JD": "鸡蛋",
    "M": "豆粕", "MA": "甲醇", "MEG": "乙二醇", "PF": "短纤", "PR": "瓶片",
    "PTA": "PTA", "PX": "对二甲苯", "SA": "纯碱", "UR": "尿素",
}


def discover(data_dir):
    """自动发现 data/ 下含 main.csv 的品种代码。"""
    codes = []
    for p in sorted(glob.glob(os.path.join(data_dir, "*", ""))):
        code = os.path.basename(p.rstrip("/\\"))
        if os.path.exists(os.path.join(p, "main.csv")):
            codes.append(code)
    return codes


def load(code, data_dir):
    p = os.path.join(data_dir, code, "main.csv")
    rows = []
    with open(p, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                o = float(r["开盘价"]); h = float(r["最高价"])
                l = float(r["最低价"]); c = float(r["收盘价"])
            except (ValueError, KeyError):
                continue
            rows.append((o, h, l, c))
    return rows


def tr(h, l, c, pc):
    return max(h - l, abs(h - pc), abs(l - pc))


def analyze(code, rows, window):
    if not rows:
        return None
    closes = [r[3] for r in rows]
    atr = []
    pc = closes[0]
    for o, h, l, c in rows:
        atr.append(tr(h, l, c, pc)); pc = c
    w = min(window, len(rows))
    atr_win = atr[-w:]; rows_win = rows[-w:]
    atr14 = statistics.mean(atr_win)
    last_c = closes[-1]
    atr_pct = atr14 / last_c * 100
    intraday = [(h - l) / c * 100 for o, h, l, c in rows_win]
    intraday_pct = statistics.mean(intraday)
    chop = 0; n = 0
    for o, h, l, c in rows_win:
        rng = h - l
        if rng <= 0:
            continue
        n += 1
        if abs(c - o) / rng < 0.35:
            chop += 1
    chop_rate = chop / n * 100 if n else 0
    rev = 0
    for o, h, l, c in rows_win:
        rng = h - l
        if rng <= 0:
            continue
        pos = (c - l) / rng
        if c > o and pos < 0.4:       # 收阳却收在下部=上影长=假突破洗盘
            rev += 1
        elif c < o and pos > 0.6:     # 收阴却收在上部=下影长=反向洗盘
            rev += 1
    rev_rate = rev / n * 100 if n else 0
    return dict(code=code, name=NAMES.get(code, code), last=last_c, n=len(rows),
                atr_pct=atr_pct, intraday_pct=intraday_pct,
                chop_rate=chop_rate, rev_rate=rev_rate)


def friendliness(res):
    def norm(vals):
        lo, hi = min(vals), max(vals)
        if hi == lo:
            return [100] * len(vals)
        return [(v - lo) / (hi - lo) * 100 for v in vals]
    atr_n = norm([r["atr_pct"] for r in res])
    int_n = norm([r["intraday_pct"] for r in res])
    rev_n = norm([r["rev_rate"] for r in res])
    for i, r in enumerate(res):
        r["friendly"] = round(100 - (atr_n[i] + int_n[i] + rev_n[i]) / 3, 1)
    res.sort(key=lambda x: x["friendly"], reverse=True)
    return res


def main():
    ap = argparse.ArgumentParser(description="波动友好度扫描（全品种排名）")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--today", default=None, help="数据截至日，用于报告头标注")
    ap.add_argument("--window", type=int, default=60, help="回看窗口（交易日）")
    ap.add_argument("--md", action="store_true", help="额外打印 markdown 表")
    args = ap.parse_args()

    codes = discover(args.data_dir)
    res = [analyze(c, load(c, args.data_dir), args.window) for c in codes]
    res = [r for r in res if r]
    res = friendliness(res)

    print(f"{'排名':<4}{'品种':<8}{'收盘':>9}{'ATR%':>8}{'日内幅%':>9}{'搓揉率%':>9}{'反转率%':>9}{'友好度':>8}")
    for i, r in enumerate(res, 1):
        print(f"{i:<4}{r['name']:<8}{r['last']:>9.0f}{r['atr_pct']:>8.2f}{r['intraday_pct']:>9.2f}{r['chop_rate']:>9.1f}{r['rev_rate']:>9.1f}{r['friendly']:>8.1f}")
    print(f"\n注：ATR%/日内幅%/搓揉率/反转率越低=波动越干净；友好度=100-三项归一化均值（组内相对分，随参与品种变化）。窗口=近{args.window}日。")
    if args.today:
        print(f"报告日：{args.today}；请确认期货数据已更新至该日（否则排名为旧数据）。")

    if args.md:
        print("\n--- MARKDOWN ---")
        print("| 排名 | 品种 | 代码 | 收盘 | ATR% | 日内振幅% | 搓揉率% | 反转率% | 友好度 |")
        print("|---|---|---|---|---|---|---|---|---|")
        for i, r in enumerate(res, 1):
            print(f"| {i} | {r['name']} | {r['code']} | {r['last']:.0f} | {r['atr_pct']:.2f} | {r['intraday_pct']:.2f} | {r['chop_rate']:.1f} | {r['rev_rate']:.1f} | {r['friendly']:.1f} |")
        short = [r['code'] for r in res if r['n'] < args.window]
        note = f"\n> 口径：ATR%/日内幅%/搓揉率/反转率越低=波动越干净；友好度=100-三项归一化均值（组内相对分）。窗口=近{args.window}日。"
        if short:
            note += f" ⚠️ 数据长度<{args.window}日的品种（{','.join(short)}）代表性较弱，排名仅供参考。"
        print(note)


if __name__ == "__main__":
    main()
