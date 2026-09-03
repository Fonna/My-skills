#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_completeness.py — 投资复盘 Pipeline · Stage 1 数据完整性检查（信号 + 龙虎榜）

复盘前必跑：确保数据完整，不齐则补全。对指定品种逐一检查：
  - signals.json        ：存在 + fetch_date == 今天（信号新鲜度）
  - position_ranking.csv：存在 + 文件 mtime == 今天（龙虎榜完整性；CSV 无日期列，以 mtime 为新鲜度代理）
  - ai_report.md        ：存在（信息项，缺失不影响复盘骨架，但全景分析可引用）

退出码：
  0 = 完整（可进入 Stage 2）
  1 = 不完整且未自动补全（应触发补全 / 询问用户）
  2 = 错误 / 无法判定

--auto-fix：对缺失/过期的品种自动补全——
  - 龙虎榜缺失/过期    → `uv run python -m fetch.run_all <varieties>`（重抓 akshare 原始 + 99qh 龙虎榜）
  - signals 过期        → 追加 `uv run python -m analyze.run_analyze <varieties>`（重算 signals.json）
  补全后自动重新检查一遍并回报结果。

用法：
  python check_completeness.py --data-dir data --varieties FG SA PTA MA JD --today 2026-07-29
  python check_completeness.py --data-dir data --varieties FG SA PTA MA JD --auto-fix
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime


def load_fetch_date(data_dir, variety):
    path = os.path.join(data_dir, variety, "signals.json")
    if not os.path.isfile(path):
        return None, f"缺失 signals.json: {path}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:  # noqa: BLE001
        return None, f"解析失败: {path} ({e})"
    fd = d.get("fetch_date")
    if isinstance(fd, list):
        val = fd[-1] if fd else None
    else:
        val = fd
    if val is None:
        return None, "fetch_date 为 null"
    return str(val), None


def parse_date(s):
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def file_mtime_date(path):
    return date.fromtimestamp(os.path.getmtime(path))


def check_variety(data_dir, variety, today):
    """返回 dict：各维度状态。"""
    res = {"variety": variety}

    # 1) signals.json 新鲜度
    fd_str, err = load_fetch_date(data_dir, variety)
    if err:
        res["signals"] = ("❌", err)
    else:
        fd = parse_date(fd_str)
        if fd is None:
            res["signals"] = ("❌", f"fetch_date 无法解析: {fd_str}")
        else:
            delta = (today - fd).days
            if delta == 0:
                res["signals"] = ("✅", f"新鲜 {fd_str}")
            elif delta > 0:
                res["signals"] = ("⚠️", f"过期 {delta} 天 ({fd_str})")
            else:
                res["signals"] = ("🔮", f"未来 {abs(delta)} 天 ({fd_str})")

    # 2) position_ranking.csv 完整性（龙虎榜，mtime 代理新鲜度）
    rank_path = os.path.join(data_dir, variety, "position_ranking.csv")
    if not os.path.isfile(rank_path):
        res["ranking"] = ("❌", "缺失 position_ranking.csv（龙虎榜未抓）")
    else:
        m = file_mtime_date(rank_path)
        delta = (today - m).days
        if delta == 0:
            res["ranking"] = ("✅", f"今日已抓 (mtime {m.isoformat()})")
        elif delta > 0:
            res["ranking"] = ("⚠️", f"过期 {delta} 天 (mtime {m.isoformat()})")
        else:
            res["ranking"] = ("🔮", f"未来 {abs(delta)} 天 (mtime {m.isoformat()})")

    # 3) ai_report.md（信息项）
    ai_path = os.path.join(data_dir, variety, "ai_report.md")
    res["aireport"] = ("✅" if os.path.isfile(ai_path) else "➖", "ai_report.md")

    return res


def is_complete(res):
    sig = res["signals"][0]
    rk = res["ranking"][0]
    return sig in ("✅",) and rk in ("✅",)


def print_report(results):
    print(f"{'品种':<6} {'signals.json':<22} {'position_ranking(龙虎榜)':<32} ai_report")
    print("-" * 86)
    for r in results:
        print(f"{r['variety']:<6} {r['signals'][1]:<22} {r['ranking'][1]:<32} {r['aireport'][1]}")
    print("-" * 86)


def auto_fix(data_dir, varieties, today):
    root = os.path.dirname(os.path.abspath(data_dir))
    need_ranking = []
    need_signals = []
    for v in varieties:
        # 重新评估（基于当前文件状态）
        r = check_variety(data_dir, v, today)
        if r["ranking"][0] in ("❌", "⚠️"):
            need_ranking.append(v)
        if r["signals"][0] in ("❌", "⚠️"):
            need_signals.append(v)

    if need_ranking:
        print(f"\n[auto-fix] 重抓 akshare 原始 + 99qh 龙虎榜：{need_ranking}")
        subprocess.run(
            ["uv", "run", "python", "-m", "fetch.run_all", *need_ranking],
            cwd=root, check=False,
        )
    if need_signals:
        print(f"\n[auto-fix] 重算 signals.json：{need_signals}")
        subprocess.run(
            ["uv", "run", "python", "-m", "analyze.run_analyze", *need_signals],
            cwd=root, check=False,
        )
    if not need_ranking and not need_signals:
        print("\n[auto-fix] 无需补全。")


def main():
    ap = argparse.ArgumentParser(description="检查 futures_workbench 数据完整性（信号+龙虎榜）")
    ap.add_argument("--data-dir", required=True, help="futures_workbench 的 data 目录")
    ap.add_argument("--varieties", required=True, nargs="+", help="品种代码，如 FG SA PTA MA JD")
    ap.add_argument("--today", default=date.today().strftime("%Y-%m-%d"), help="今天日期 YYYY-MM-DD")
    ap.add_argument("--auto-fix", action="store_true", help="缺失/过期时自动补全并重检")
    args = ap.parse_args()

    today = parse_date(args.today)
    if today is None:
        print(f"[ERR] --today 无法解析: {args.today}", file=sys.stderr)
        sys.exit(2)

    results = [check_variety(args.data_dir, v, today) for v in args.varieties]
    print_report(results)

    incomplete = [r for r in results if not is_complete(r)]
    if incomplete:
        names = [r["variety"] for r in incomplete]
        if args.auto_fix:
            auto_fix(args.data_dir, names, today)
            # 重检
            results2 = [check_variety(args.data_dir, v, today) for v in args.varieties]
            print("\n=== 补全后重新检查 ===")
            print_report(results2)
            if all(is_complete(r) for r in results2):
                print("结论：补全后全部完整，可进入 Stage 2。")
                sys.exit(0)
            else:
                print("结论：补全后仍有缺口，请检查 fetch 日志或手动补全。")
                sys.exit(1)
        else:
            print(f"结论：{len(incomplete)} 个品种数据不完整（{names}），应先补全或询问用户。")
            sys.exit(1)
    else:
        print("结论：全部完整，可进入 Stage 2（数据处理）。")
        sys.exit(0)


if __name__ == "__main__":
    main()
