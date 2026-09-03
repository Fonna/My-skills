#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_tech_snapshot.py — 投资复盘 Pipeline · Stage 3 双轨 HTML 看板生成

扫描 futures_workbench/data/<品种>/signals.json，提取技术字段，渲染深色表格 HTML，
高亮聚焦品种（默认 FG SA PTA MA JD）。输出到 --out 指定的素材文件。

用法：
  python gen_tech_snapshot.py --data-dir data --out 素材/2026-07-23_跨品种技术面快照.html \
      --focus FG SA PTA MA JD --title "跨品种技术面快照 2026-07-23"

说明：
  - signals.json 为扁平结构（field -> list），取 [-1] 为最新。
  - None 渲染为 "—"。
  - 双轨归档：HTML 进素材/，另需写一份 md 摘要进 投资/（见 report-templates.md B）。
"""
import argparse
import glob
import html
import json
import os

FIELDS = [
    ("contract_code", "合约"),
    ("fetch_date", "日期"),
    ("close", "收盘"),
    ("ma20", "MA20"),
    ("ma60", "MA60"),
    ("ma120", "MA120"),
    ("rsi14", "RSI14"),
    ("pct_5y", "5y分位%"),
    ("trend", "趋势"),
    ("regime", "风控"),
]


def last(d, key):
    v = d.get(key)
    if isinstance(v, list):
        return v[-1] if v else None
    return v


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def build_rows(data_dir, focus):
    rows = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*", "signals.json"))):
        variety = os.path.basename(os.path.dirname(path))
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:  # noqa: BLE001
            continue
        cells = {label: fmt(last(d, key)) for key, label in FIELDS}
        rows.append((variety, variety in focus, cells))
    return rows


def render(rows, title):
    body = []
    for variety, is_focus, cells in rows:
        cls = ' class="focus"' if is_focus else ""
        tds = "".join(f"<td>{html.escape(cells[lbl])}</td>" for _, lbl in FIELDS)
        body.append(f'<tr{cls}><td class="var">{html.escape(variety)}</td>{tds}</tr>')
    headers = "".join(f"<th>{lbl}</th>" for _, lbl in FIELDS)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  body {{ background:#0f1419; color:#e6e6e6; font-family:-apple-system,"Segoe UI",Roboto,"PingFang SC",sans-serif; margin:0; padding:24px; }}
  h1 {{ font-size:18px; font-weight:600; margin:0 0 4px; color:#fff; }}
  .sub {{ color:#8b98a5; font-size:12px; margin-bottom:16px; }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; }}
  th, td {{ padding:8px 10px; text-align:right; border-bottom:1px solid #1e2730; white-space:nowrap; }}
  th {{ color:#8b98a5; font-weight:500; position:sticky; top:0; background:#0f1419; }}
  td.var, th:first-child {{ text-align:left; font-weight:600; }}
  tr.focus td.var {{ color:#ffb347; }}
  tr.focus {{ background:rgba(255,179,71,0.08); }}
  tr:hover td {{ background:rgba(255,255,255,0.03); }}
</style></head>
<body>
<h1>{html.escape(title)}</h1>
<div class="sub">双轨归档 · 数据 sourced from futures_workbench signals.json · 聚焦品种高亮</div>
<table>
<thead><tr><th>品种</th>{headers}</tr></thead>
<tbody>
{''.join(body)}
</tbody>
</table>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="生成跨品种技术面 HTML 看板")
    ap.add_argument("--data-dir", required=True, help="futures_workbench 的 data 目录")
    ap.add_argument("--out", required=True, help="输出 HTML 路径（建议 素材/YYYY-MM-DD_跨品种技术面快照.html）")
    ap.add_argument("--focus", nargs="*", default=["FG", "SA", "PTA", "MA", "JD"], help="高亮品种")
    ap.add_argument("--title", default="跨品种技术面快照", help="页面标题")
    args = ap.parse_args()

    rows = build_rows(args.data_dir, set(args.focus))
    if not rows:
        print("[ERR] 未扫描到任何 signals.json", file=__import__("sys").stderr)
        __import__("sys").exit(2)

    out = render(rows, args.title)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"✅ 已生成 {args.out}（{len(rows)} 品种，聚焦 {len(args.focus)}）")


if __name__ == "__main__":
    main()
