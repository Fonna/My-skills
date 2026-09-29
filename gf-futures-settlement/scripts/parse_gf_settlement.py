#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""广发期货交易结算单解析器。

输入：Outlook MCP 下载的附件资源 JSON（含 contentBytes，base64+GBK 编码的结算单文本），
      或已解码的 UTF-8 结算单 txt。
输出：
  - gf_settlement_<日期>.txt   解码后的 UTF-8 结算单全文（--json 输入时）
  - gf_settlement_<日期>.json  结构化数据（资金、实际盈亏、浮盈浮亏、成交、持仓）
  - settlement_summary.csv     按日汇总（幂等：同日期覆盖），供长期趋势分析
  - trades.csv                 成交流水（按成交序号去重追加）

用法：
  python parse_gf_settlement.py --json raw.json [--out-dir DIR] [--csv-dir DIR]
  python parse_gf_settlement.py --txt gf_settlement_20260928.txt [--out-dir DIR]
"""
import argparse
import base64
import csv
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 常见品种合约乘数（吨/手）。未收录品种会从结算单 MTM 反推并给出 warning。
KNOWN_MULT = {
    "FG": 20, "SA": 20, "MA": 10, "UR": 20, "TA": 5, "PTA": 5, "JD": 10,
    "SR": 10, "CF": 5, "AP": 10, "CJ": 10, "OI": 10, "RM": 10, "C": 10,
    "CS": 10, "I": 100, "J": 100, "JM": 60, "PP": 5, "EG": 10, "EB": 5,
    "PG": 20, "L": 5, "V": 5, "PF": 5, "PX": 5, "SH": 30, "EC": 50,
}
VALID_MULTS = {5, 10, 15, 20, 25, 30, 50, 60, 100}

SUMMARY_COLUMNS = [
    "settlement_date", "opening_balance", "deposit_withdrawal", "realized_pnl",
    "floating_pnl_at_settle", "mtm_pnl_today", "fee", "net_change",
    "closing_balance", "equity", "margin_occupied", "available_funds",
    "risk_degree_pct", "open_positions",
]
TRADE_COLUMNS = [
    "settlement_date", "trans_no", "product", "contract", "bs", "oc",
    "price", "lots", "turnover", "fee", "realized_pnl",
]


def fnum(s):
    s = (s or "").strip().replace(",", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def inum(s):
    v = fnum(s)
    return int(round(v))


def load_text(args):
    """返回 (text, 需要写出的解码 txt 或 None)。"""
    if args.txt:
        p = Path(args.txt)
        return p.read_text(encoding="utf-8-sig"), None
    p = Path(args.json)
    raw = p.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    b64 = data.get("contentBytes")
    if not b64:
        raise SystemExit("JSON 中没有 contentBytes 字段（确认下载的是附件资源本身）")
    blob = base64.b64decode(b64)
    text = blob.decode("gbk", errors="replace")
    if "\ufffd" in text:
        print("[warn] GBK 解码出现替换符，个别字符可能失真", file=sys.stderr)
    return text, text


def grab(text, pattern, cast=float):
    m = re.search(pattern, text)
    if not m:
        return None
    return cast(m.group(1).replace(",", "")) if cast is float else m.group(1)


def section_rows(text, header):
    """截取节头之后、下一节头/结尾之前的所有竖线行，切成 cells 列表。"""
    idx = text.find(header)
    if idx < 0:
        return []
    nxt = [text.find(h, idx + len(header)) for h in
           ("成交记录 Transaction Record", "平仓明细 Position Closed", "持仓汇总 Positions")]
    nxt = [x for x in nxt if x > 0]
    end = min(nxt) if nxt else len(text)
    rows = []
    for line in text[idx:end].splitlines():
        line = line.strip()
        if line.startswith("|") and line.rstrip().endswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            rows.append(cells)
    return rows


def data_rows(rows, first_cell_re):
    out = []
    for cells in rows:
        if len(cells) < 8:
            continue
        first = cells[0]
        if first.startswith("共"):
            continue
        if re.fullmatch(first_cell_re, first):
            out.append(cells)
    return out


def parse_transactions(text):
    recs = []
    for c in data_rows(section_rows(text, "成交记录 Transaction Record"), r"\d{8}"):
        if len(c) < 17:
            continue
        recs.append({
            "date": c[0], "exchange": c[2], "trade_code": c[3],
            "product": c[4], "contract": c[5], "bs": c[6], "sh": c[7],
            "price": fnum(c[8]), "lots": inum(c[9]), "turnover": fnum(c[10]),
            "oc": c[11], "fee": fnum(c[12]), "realized_pnl": fnum(c[13]),
            "trans_no": c[15], "account": c[16],
        })
    return recs


def parse_closed(text):
    recs = []
    for c in data_rows(section_rows(text, "平仓明细 Position Closed"), r"\d{8}"):
        if len(c) < 16:
            continue
        recs.append({
            "close_date": c[0], "product": c[4], "contract": c[5],
            "open_date": c[6], "close_side": c[8],  # 买=买入平空仓, 卖=卖出平多仓
            "position_dir": "空" if c[8] == "买" else ("多" if c[8] == "卖" else c[8]),
            "lots": inum(c[9]), "open_price": fnum(c[10]),
            "prev_settle": fnum(c[11]), "close_price": fnum(c[12]),
            "realized_pnl": fnum(c[13]), "account": c[15],
        })
    return recs


def resolve_multiplier(code, avg_open, prev_s, today_s, mtm, warnings):
    """返回 (multiplier, basis)。basis: 'prev'=持仓隔日盯市口径, 'open'=当日开仓口径。"""
    known = KNOWN_MULT.get(code)
    cands = {}
    for basis, delta in (("prev", prev_s - today_s), ("open", avg_open - today_s)):
        if abs(delta) > 1e-9 and abs(mtm) > 1e-9:
            m = abs(mtm) / abs(delta)
            r = int(round(m))
            if r > 0 and abs(m - r) < 0.02 and (r in VALID_MULTS or r == known):
                cands.setdefault(basis, r)
    if known:
        for basis in ("prev", "open"):
            if cands.get(basis) == known:
                return known, basis
        return known, "known"  # MTM 为 0 等无法反推时，信任品种表
    vals = set(cands.values())
    if len(vals) == 1:
        return cands[[b for b in ("prev", "open") if b in cands][0]], \
               [b for b in ("prev", "open") if b in cands][0]
    if not vals:
        warnings.append(f"{code}: 无法从 MTM 反推合约乘数，浮盈浮亏按 0 处理")
        return None, None
    warnings.append(f"{code}: 乘数反推有歧义 {cands}，优先采用隔日盯市口径")
    return cands.get("prev", list(vals)[0]), "prev"


def parse_positions(text, warnings):
    recs = []
    for c in data_rows(section_rows(text, "持仓汇总 Positions"), r"\d+"):
        if len(c) < 16:
            continue
        long_lots, short_lots = inum(c[4]), inum(c[6])
        avg_buy, avg_sell = fnum(c[5]), fnum(c[7])
        prev_s, today_s, mtm = fnum(c[8]), fnum(c[9]), fnum(c[10])
        if long_lots == 0 and short_lots == 0:
            continue
        direction = "多" if long_lots > 0 else "空"
        lots = long_lots if long_lots > 0 else short_lots
        avg_open = avg_buy if long_lots > 0 else avg_sell
        code = re.match(r"^[A-Za-z]+", c[5])
        code = code.group(1).upper() if code else c[5].upper()
        mult, basis = resolve_multiplier(code, avg_open, prev_s, today_s, mtm, warnings)
        floating = None
        if mult:
            diff = (today_s - avg_open) if direction == "多" else (avg_open - today_s)
            floating = round(diff * lots * mult, 2)
        # 持仓表无日期列：|投资单元|交易编码|品种|合约|买持|买开均价|卖持|卖开均价|昨结|今结|盯市|保证金|投保|多市值|空市值|账号|
        recs.append({
            "product": c[2], "contract": c[3], "direction": direction,
            "lots": lots, "avg_open_price": avg_open,
            "prev_settle": prev_s, "today_settle": today_s,
            "mtm_today": mtm, "margin": fnum(c[11]),
            "multiplier": mult, "mult_basis": basis,
            "floating_pnl_at_settle": floating,
        })
    return recs


def build_record(text, warnings):
    date = grab(text, r"日期 Date：\s*(\d{8})", str)
    if not date:
        raise SystemExit("未找到「日期 Date：」行，确认是广发期货结算单文本")
    rec = {
        "settlement_date": date,
        "account_id": grab(text, r"客户号 Client ID：\s*(\d+)", str),
        "client_name": grab(text, r"客户名称 Client Name：\s*(\S+)", str),
        "balance": {
            "opening": grab(text, r"期初结存 Balance B/F：\s*(-?[\d,]+(?:\.\d+)?)"),
            "closing": grab(text, r"期末结存 Balance C/F：\s*(-?[\d,]+(?:\.\d+)?)"),
            "deposit_withdrawal": grab(text, r"出 入 金 Deposit/Withdrawal：\s*(-?[\d,]+(?:\.\d+)?)"),
            "equity": grab(text, r"客户权益 Client Equity：\s*(-?[\d,]+(?:\.\d+)?)"),
        },
        "pnl": {
            "realized": grab(text, r"平仓盈亏 Realized P/L：\s*(-?[\d,]+(?:\.\d+)?)"),
            "mtm_today": grab(text, r"持仓盯市盈亏 MTM P/L：\s*(-?[\d,]+(?:\.\d+)?)"),
            "fee": grab(text, r"手 续 费 Commission：\s*(-?[\d,]+(?:\.\d+)?)"),
        },
        "margin": {
            "occupied": grab(text, r"保证金占用 Margin Occupied：\s*(-?[\d,]+(?:\.\d+)?)"),
            "available": grab(text, r"可用资金 Fund Avail\.：\s*(-?[\d,]+(?:\.\d+)?)"),
            "risk_degree_pct": grab(text, r"风 险 度 Risk Degree：\s*([\d.]+)%"),
        },
    }
    rec["transactions"] = parse_transactions(text)
    for t in rec["transactions"]:
        t["settlement_date"] = date
    rec["closed_positions"] = parse_closed(text)
    rec["open_positions"] = parse_positions(text, warnings)
    rec["warnings"] = warnings

    b, p = rec["balance"], rec["pnl"]
    rec["derived"] = {
        "net_change": round(b["closing"] - b["opening"] - b["deposit_withdrawal"], 2),
        "fee_total_from_trades": round(sum(t["fee"] for t in rec["transactions"]), 2),
        "realized_total_from_closes": round(sum(x["realized_pnl"] for x in rec["closed_positions"]), 2),
        "mtm_total_from_positions": round(sum(x["mtm_today"] for x in rec["open_positions"]), 2),
        "floating_pnl_total": round(sum(x["floating_pnl_at_settle"] or 0 for x in rec["open_positions"]), 2),
    }
    d = rec["derived"]
    d["checks"] = [
        {"name": "fee 与成交流水一致", "ok": abs(d["fee_total_from_trades"] - p["fee"]) < 0.01},
        {"name": "平仓盈亏与平仓明细一致", "ok": abs(d["realized_total_from_closes"] - p["realized"]) < 0.01},
        {"name": "盯市盈亏与持仓汇总一致", "ok": abs(d["mtm_total_from_positions"] - p["mtm_today"]) < 0.01},
        {"name": "权益勾稽(期初+出入金+实际-盯市-手续费)",
         "ok": abs(b["opening"] + b["deposit_withdrawal"] + p["realized"]
                   + p["mtm_today"] - p["fee"] - b["closing"]) < 0.02},
    ]
    return rec


def update_summary_csv(csv_dir, rec):
    path = Path(csv_dir) / "settlement_summary.csv"
    rows = []
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rows = [r for r in csv.DictReader(fh)]
    rows = [r for r in rows if r["settlement_date"] != rec["settlement_date"]]
    rows.append({
        "settlement_date": rec["settlement_date"],
        "opening_balance": rec["balance"]["opening"],
        "deposit_withdrawal": rec["balance"]["deposit_withdrawal"],
        "realized_pnl": rec["pnl"]["realized"],
        "floating_pnl_at_settle": rec["derived"]["floating_pnl_total"],
        "mtm_pnl_today": rec["pnl"]["mtm_today"],
        "fee": rec["pnl"]["fee"],
        "net_change": rec["derived"]["net_change"],
        "closing_balance": rec["balance"]["closing"],
        "equity": rec["balance"]["equity"],
        "margin_occupied": rec["margin"]["occupied"],
        "available_funds": rec["margin"]["available"],
        "risk_degree_pct": rec["margin"]["risk_degree_pct"],
        "open_positions": len(rec["open_positions"]),
    })
    rows.sort(key=lambda r: r["settlement_date"])
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SUMMARY_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return path


def update_trades_csv(csv_dir, rec):
    path = Path(csv_dir) / "trades.csv"
    seen = set()
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as fh:
            seen = {r["trans_no"] for r in csv.DictReader(fh) if r.get("trans_no")}
    new = [t for t in rec["transactions"] if t["trans_no"] and t["trans_no"] not in seen]
    if not new:
        return path, 0
    exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=TRADE_COLUMNS)
        if not exists:
            w.writeheader()
        for t in new:
            w.writerow({k: t[k] for k in TRADE_COLUMNS})
    return path, len(new)


def main():
    ap = argparse.ArgumentParser(description="解析广发期货结算单")
    ap.add_argument("--json", help="Outlook 下载的附件资源 JSON（contentBytes）")
    ap.add_argument("--txt", help="已解码的 UTF-8 结算单文本")
    ap.add_argument("--out-dir", help="输出目录，默认与输入同目录")
    ap.add_argument("--csv-dir", help="汇总 CSV 目录，默认与 --out-dir 相同")
    args = ap.parse_args()
    if not args.json and not args.txt:
        ap.error("必须提供 --json 或 --txt 之一")

    warnings = []
    text, decoded = load_text(args)
    out_dir = Path(args.out_dir) if args.out_dir else Path(args.json or args.txt).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_dir = Path(args.csv_dir) if args.csv_dir else out_dir

    rec = build_record(text, warnings)
    files = {}
    if decoded is not None:
        txt_path = out_dir / f"gf_settlement_{rec['settlement_date']}.txt"
        txt_path.write_text(decoded, encoding="utf-8")
        files["txt"] = str(txt_path)
    json_path = out_dir / f"gf_settlement_{rec['settlement_date']}.json"
    json_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    files["json"] = str(json_path)
    files["summary_csv"] = str(update_summary_csv(csv_dir, rec))
    _, n = update_trades_csv(csv_dir, rec)
    files["trades_csv"] = str(Path(files["summary_csv"]).parent / "trades.csv")

    b, p, d = rec["balance"], rec["pnl"], rec["derived"]
    print(f"结算日 {rec['settlement_date']}  账户 {rec['account_id']}  {rec['client_name']}")
    print(f"期初结存 {b['opening']:.2f} -> 期末结存 {b['closing']:.2f} | 客户权益 {b['equity']:.2f}"
          f" | 出入金 {b['deposit_withdrawal']:.2f}")
    print(f"实际盈亏(平仓) {p['realized']:+.2f} | 当日盯市 {p['mtm_today']:+.2f}"
          f" | 手续费 {p['fee']:.2f} | 当日净变动 {d['net_change']:+.2f}")
    print(f"浮盈浮亏(按今结算) {d['floating_pnl_total']:+.2f}"
          f" | 保证金占用 {rec['margin']['occupied']:.2f} | 可用 {rec['margin']['available']:.2f}"
          f" | 风险度 {rec['margin']['risk_degree_pct']}%")
    for pos in rec["open_positions"]:
        print(f"  持仓 {pos['contract']} {pos['direction']} {pos['lots']}手"
              f" 开均价{pos['avg_open_price']} 今结{pos['today_settle']}"
              f" 乘数{pos['multiplier']} 当日盯市{pos['mtm_today']:+.2f}"
              f" 浮动{pos['floating_pnl_at_settle']:+.2f}")
    for c in d["checks"]:
        print(f"  [{'OK' if c['ok'] else 'FAIL'}] {c['name']}")
    for w in warnings:
        print(f"  [warn] {w}")
    print("输出文件:")
    for k, v in files.items():
        print(f"  {k}: {v}")
    if n:
        print(f"  trades.csv 新增 {n} 条成交")


if __name__ == "__main__":
    main()
