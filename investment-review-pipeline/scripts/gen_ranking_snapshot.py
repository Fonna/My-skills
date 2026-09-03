#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_ranking_snapshot.py — 投资复盘 Pipeline · 龙虎榜双轨 HTML 看板生成

扫描 futures_workbench/data/<品种>/position_ranking.csv（99qh 期货公司会员持仓排名），
提取多空合计、净持仓、净变动、TOP5 多/空席位，渲染深色表格 HTML，
高亮聚焦品种（默认 FG SA PTA MA JD）。输出到 --out 指定的素材文件。

用法：
  python gen_ranking_snapshot.py --data-dir data --out 素材/2026-07-29_龙虎榜快照.html \
      --focus FG SA PTA MA JD --title "99qh 龙虎榜快照 2026-07-29"

说明：
  - position_ranking.csv 列：contract,side,isTotal,rank,name,member_id,position,
    positionChange,netPosition,netPositionChange,netPositionVal
    （含 BOM，按 utf-8-sig 读；isTotal=1 为合计行，分析时剔除）
  - 净持仓 = 空头合计 - 多头合计；净变动 = 空头变动合计 - 多头变动合计
  - None / 空 渲染为 "—"
  - 双轨归档：HTML 进素材/，另需写一份 md 摘要进 投资/（见 report-templates.md B2）
"""
import argparse
import csv
import glob
import html
import os

FOCUS_DEFAULT = ["FG", "SA", "PTA", "MA", "JD"]


def load_variety(data_dir, variety):
    path = os.path.join(data_dir, variety, "position_ranking.csv")
    if not os.path.isfile(path):
        return None
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if str(r.get("isTotal", "")).strip() == "1":
                continue  # 剔除合计行
            rows.append(r)
    if not rows:
        return None
    contract = rows[0].get("contract", "")
    longs = [r for r in rows if r.get("side") == "long"]
    shorts = [r for r in rows if r.get("side") == "short"]

    def num(r, k):
        try:
            return int(float(r.get(k) or 0))
        except (ValueError, TypeError):
            return 0

    long_total = sum(num(r, "position") for r in longs)
    short_total = sum(num(r, "position") for r in shorts)
    long_chg = sum(num(r, "positionChange") for r in longs)
    short_chg = sum(num(r, "positionChange") for r in shorts)
    # 期货龙虎榜惯例：净持仓 = 多头合计 − 空头合计（净空为负）；净变动 = 多头变动 − 空头变动
    net = long_total - short_total
    net_chg = long_chg - short_chg

    def top(lst, n=5):
        s = sorted(lst, key=lambda r: num(r, "position"), reverse=True)[:n]
        return [(r.get("name", ""), num(r, "position"), num(r, "positionChange")) for r in s]

    return {
        "contract": contract,
        "long_total": long_total,
        "short_total": short_total,
        "net": net,
        "long_chg": long_chg,
        "short_chg": short_chg,
        "net_chg": net_chg,
        "top_long": top(longs),
        "top_short": top(shorts),
    }


def fmt_int(v):
    return f"{v:,}" if isinstance(v, int) else (f"{v:,.0f}" if isinstance(v, float) else "—")


def fmt_chg(v):
    if v == 0:
        return "0"
    return f"+{v:,}" if v > 0 else f"{v:,}"


def render(varieties_data, title, focus):
    # 摘要表
    sum_rows = []
    for v, d in varieties_data:
        cls = ' class="focus"' if v in focus else ""
        net_cls = "neg" if d["net"] < 0 else "pos"
        sum_rows.append(
            f'<tr{cls}><td class="var">{html.escape(v)}</td>'
            f'<td>{html.escape(d["contract"])}</td>'
            f'<td class="num">{fmt_int(d["long_total"])}</td>'
            f'<td class="num">{fmt_int(d["short_total"])}</td>'
            f'<td class="num {net_cls}">{fmt_int(d["net"])}</td>'
            f'<td class="num">{fmt_chg(d["net_chg"])}</td>'
            f'<td>{judge(d)}</td></tr>'
        )

    # 分品种块（聚焦优先）
    blocks = []
    ordered = sorted(varieties_data, key=lambda x: (x[0] not in focus, x[0]))
    for v, d in ordered:
        is_focus = v in focus
        block_cls = ' class="focus"' if is_focus else ""
        long_html = "".join(
            f'<tr><td>{html.escape(n)}</td><td class="num">{fmt_int(p)}</td>'
            f'<td class="num chg">{fmt_chg(c)}</td></tr>'
            for n, p, c in d["top_long"]
        )
        short_html = "".join(
            f'<tr><td>{html.escape(n)}</td><td class="num">{fmt_int(p)}</td>'
            f'<td class="num chg">{fmt_chg(c)}</td></tr>'
            for n, p, c in d["top_short"]
        )
        blocks.append(f"""
<div class="block"{block_cls}>
  <h2>{html.escape(v)} · <span class="code">{html.escape(d["contract"])}</span>
      <span class="tag">{'聚焦' if is_focus else '常规'}</span></h2>
  <div class="totals">多头合计 <b>{fmt_int(d["long_total"])}</b> ｜ 空头合计 <b>{fmt_int(d["short_total"])}</b>
      ｜ 净持仓 <b class="{'neg' if d['net']<0 else 'pos'}">{fmt_int(d['net'])}</b>
      ｜ 净变动 <b>{fmt_chg(d['net_chg'])}</b></div>
  <div class="two">
    <table><thead><tr><th>TOP5 多头席位</th><th>持仓</th><th>变动</th></tr></thead>
      <tbody>{long_html}</tbody></table>
    <table><thead><tr><th>TOP5 空头席位</th><th>持仓</th><th>变动</th></tr></thead>
      <tbody>{short_html}</tbody></table>
  </div>
  <div class="judge">判读：{judge(d)}</div>
</div>""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  body {{ background:#0f1419; color:#e6e6e6; font-family:-apple-system,"Segoe UI",Roboto,"PingFang SC",sans-serif; margin:0; padding:24px; }}
  h1 {{ font-size:18px; font-weight:600; margin:0 0 4px; color:#fff; }}
  .sub {{ color:#8b98a5; font-size:12px; margin-bottom:16px; }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; }}
  th, td {{ padding:7px 10px; text-align:right; border-bottom:1px solid #1e2730; white-space:nowrap; }}
  th {{ color:#8b98a5; font-weight:500; }}
  td.var, th:first-child {{ text-align:left; font-weight:600; }}
  .num {{ font-variant-numeric:tabular-nums; }}
  .neg {{ color:#ff7b7b; }}
  .pos {{ color:#7bed9f; }}
  .chg.pos {{ color:#ff7b7b; }}
  .chg.neg {{ color:#7bed9f; }}
  tr.focus td.var {{ color:#ffb347; }}
  tr.focus {{ background:rgba(255,179,71,0.08); }}
  .summary {{ margin-bottom:24px; }}
  .block {{ background:#161b22; border:1px solid #1e2730; border-radius:8px; padding:14px 16px; margin-bottom:14px; }}
  .block.focus {{ border-color:rgba(255,179,71,0.5); }}
  .block h2 {{ font-size:15px; margin:0 0 8px; color:#fff; }}
  .block .code {{ color:#8b98a5; font-weight:400; font-size:13px; }}
  .tag {{ font-size:11px; padding:1px 7px; border-radius:10px; background:#2a3441; color:#8b98a5; margin-left:6px; }}
  .block.focus .tag {{ background:rgba(255,179,71,0.2); color:#ffb347; }}
  .totals {{ font-size:13px; color:#c9d1d9; margin-bottom:10px; }}
  .two {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
  .two table th:first-child, .two table td:first-child {{ text-align:left; }}
  .judge {{ font-size:12px; color:#8b98a5; margin-top:8px; }}
  @media (max-width:680px) {{ .two {{ grid-template-columns:1fr; }} }}
</style></head>
<body>
<h1>{html.escape(title)}</h1>
<div class="sub">双轨归档 · 数据 sourced from futures_workbench position_ranking.csv（99qh 期货公司会员持仓排名，不分内外资）· 聚焦品种高亮</div>
<div class="summary">
<table>
<thead><tr><th>品种</th><th>合约</th><th>多头合计</th><th>空头合计</th><th>净持仓</th><th>净变动</th><th>判读</th></tr></thead>
<tbody>
{''.join(sum_rows)}
</tbody></table></div>
{''.join(blocks)}
</body></html>"""


def judge(d):
    net = d["net"]
    chg = d["net_chg"]
    if net < 0 and chg < 0:
        return "净空且扩大 → 偏空"
    if net < 0 and chg > 0:
        return "净空但收窄 → 空方退"
    if net > 0 and chg > 0:
        return "净多且扩大 → 偏多"
    if net > 0 and chg < 0:
        return "净多但收窄 → 多方退"
    return "中性"


def main():
    ap = argparse.ArgumentParser(description="生成 99qh 龙虎榜 HTML 看板")
    ap.add_argument("--data-dir", required=True, help="futures_workbench 的 data 目录")
    ap.add_argument("--out", required=True, help="输出 HTML 路径（建议 素材/YYYY-MM-DD_龙虎榜快照.html）")
    ap.add_argument("--focus", nargs="*", default=FOCUS_DEFAULT, help="高亮品种")
    ap.add_argument("--title", default="99qh 龙虎榜快照", help="页面标题")
    ap.add_argument("--print-summary", action="store_true", help="额外打印摘要 JSON 到 stdout")
    args = ap.parse_args()

    focus = set(args.focus)
    data = []
    for path in sorted(glob.glob(os.path.join(args.data_dir, "*", "position_ranking.csv"))):
        variety = os.path.basename(os.path.dirname(path))
        d = load_variety(args.data_dir, variety)
        if d:
            data.append((variety, d))

    if not data:
        print("[ERR] 未扫描到任何 position_ranking.csv", file=__import__("sys").stderr)
        __import__("sys").exit(2)

    out = render(data, args.title, focus)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"✅ 已生成 {args.out}（{len(data)} 品种，聚焦 {len(focus)}）")

    if args.print_summary:
        import json
        print("SUMMARY_JSON:" + json.dumps(
            {v: {k: d[k] for k in ("contract", "long_total", "short_total", "net", "net_chg")}
             for v, d in data},
            ensure_ascii=False))


if __name__ == "__main__":
    main()
