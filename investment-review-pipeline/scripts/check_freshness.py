#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_freshness.py — 投资复盘 Pipeline · Stage 1.2 数据新鲜度检查

逐品种读取 futures_workbench 的 signals.json，比对 fetch_date 与今天。
signals.json 为扁平结构（field -> list），fetch_date 最新值在 [-1]。

用法：
  python check_freshness.py --data-dir data --varieties FG SA PTA MA JD --today 2026-07-23

退出码：
  0 = 全部新鲜（可进入 Stage 2）
  1 = 存在过期品种（应触发更新 / 询问用户）
  2 = 文件缺失或解析错误
"""
import argparse
import json
import os
import sys
from datetime import date, datetime


def load_fetch_date(data_dir: str, variety: str):
    """返回 (fetch_date_str, error_or_None)。"""
    path = os.path.join(data_dir, variety, "signals.json")
    if not os.path.isfile(path):
        return None, f"缺失文件: {path}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:  # noqa: BLE001
        return None, f"解析失败: {path} ({e})"

    fd = d.get("fetch_date")
    if isinstance(fd, list):
        if not fd:
            return None, "fetch_date 为空列表"
        val = fd[-1]
    else:
        val = fd  # 兼容标量
    if val is None:
        return None, "fetch_date 为 null"
    return str(val), None


def parse_date(s: str):
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def main():
    ap = argparse.ArgumentParser(description="检查 futures_workbench signals 新鲜度")
    ap.add_argument("--data-dir", required=True, help="futures_workbench 的 data 目录")
    ap.add_argument("--varieties", required=True, nargs="+", help="品种代码列表，如 FG SA PTA MA JD")
    ap.add_argument("--today", default=date.today().strftime("%Y-%m-%d"),
                    help="今天日期 YYYY-MM-DD（默认取系统日期）")
    args = ap.parse_args()

    today = parse_date(args.today)
    if today is None:
        print(f"[ERR] --today 无法解析: {args.today}", file=sys.stderr)
        sys.exit(2)

    print(f"{'品种':<6} {'fetch_date':<12} {'偏差(天)':<10} {'状态'}")
    print("-" * 44)

    all_fresh = True
    has_error = False
    for v in args.varieties:
        fd_str, err = load_fetch_date(args.data_dir, v)
        if err:
            print(f"{v:<6} {'—':<12} {'—':<10} ❌ {err}")
            has_error = True
            all_fresh = False
            continue
        fd = parse_date(fd_str)
        if fd is None:
            print(f"{v:<6} {fd_str:<12} {'—':<10} ❌ 日期格式无法解析")
            has_error = True
            all_fresh = False
            continue
        delta = (today - fd).days
        if delta == 0:
            status = "✅ 新鲜"
        elif delta > 0:
            status = f"⚠️ 过期 {delta} 天"
            all_fresh = False
        else:
            status = f"🔮 未来 {abs(delta)} 天"
        print(f"{v:<6} {fd_str:<12} {delta:<10} {status}")

    print("-" * 44)
    if has_error:
        print("结论：存在文件/解析错误，先排查数据源。")
        sys.exit(2)
    if all_fresh:
        print("结论：全部新鲜，可进入 Stage 2（数据处理）。")
        sys.exit(0)
    else:
        print("结论：存在过期品种，应先更新期货项目数据或询问用户。")
        sys.exit(1)


if __name__ == "__main__":
    main()
