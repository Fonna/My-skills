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
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 常见品种合约乘数（吨/手）。未收录品种会从当日成交额或 MTM 反推并给出 warning。
KNOWN_MULT = {
    "FG": 20, "SA": 20, "MA": 10, "UR": 20, "TA": 5, "PTA": 5, "JD": 10,
    "SR": 10, "CF": 5, "AP": 10, "CJ": 10, "OI": 10, "RM": 10, "C": 10,
    "CS": 10, "I": 100, "J": 100, "JM": 60, "PP": 5, "EG": 10, "EB": 5,
    "PG": 20, "L": 5, "V": 5, "PF": 5, "PX": 5, "SH": 30, "EC": 50,
    # 补充常用品种，避免未收录品种触发「乘数未知 → 浮盈浮亏缺失」
    "SC": 1000, "FU": 10, "BU": 10, "LU": 10, "RU": 10, "NR": 10, "BR": 5,
    "SP": 10, "SS": 5, "LC": 1, "SI": 5, "AO": 20, "PR": 15, "PK": 5,
    "SF": 5, "SM": 5, "ZC": 100, "CU": 5, "AL": 5, "ZN": 5, "NI": 1,
    "PB": 5, "SN": 1, "AU": 1000, "AG": 15, "BC": 5,
}
VALID_MULTS = {1, 3, 5, 10, 15, 20, 25, 30, 50, 60, 100, 1000}

SUMMARY_COLUMNS = [
    "settlement_date", "opening_balance", "deposit_withdrawal", "realized_pnl",
    "floating_pnl_at_settle", "mtm_pnl_today", "fee", "net_change",
    "closing_balance", "equity", "margin_occupied", "available_funds",
    "risk_degree_pct", "open_positions",
]
TRADE_COLUMNS = [
    "settlement_date", "trans_no", "product", "contract", "bs", "oc",
    "price", "lots", "turnover", "fee", "realized_pnl",
    "open_date", "full_realized_pnl",
]

LEDGER_MD_HEADER = """# 开平仓记录（自动生成）

> 由 `gf-futures-settlement` skill 每日结算单解析后自动重建（数据源：`账户归档/结算单数据/trades.csv`），勿手工编辑。
> **口径**：`当日腿盈亏`＝结算单口径（昨结算→平仓价）；`全程盈亏`＝开仓价→平仓价（含此前各日已盯市落账部分），仅在能匹配到平仓明细/开仓记录时填写。
> 平仓行的 `开仓日/开仓价` 来自结算单「平仓明细 Position Closed」；同日开平（隔日归档无该行则开仓日=当日）均逐笔分行记录。
> 手工复盘与定性分析见 [[复盘_逐笔]]。

"""



def fnum(s):
    if isinstance(s, (int, float)):
        return float(s)
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


def contract_code(contract):
    """从合约号取品种代码（字母前缀），如 SA701 -> SA、jd2612 -> JD。"""
    s = (contract or "").strip()
    m = re.match(r"^[A-Za-z]+", s)
    return m.group(0).upper() if m else s.upper()


def known_multiplier(code, contract):
    """品种表乘数；含合约级例外（鸡蛋 JD2301 起由 5 吨/手改为 10 吨/手）。"""
    if code == "JD":
        m = re.match(r"^JD(\d{3,4})$", (contract or "").strip(), re.I)
        if m and int(m.group(1)) < 2301:
            return 5
    return KNOWN_MULT.get(code)


def mult_from_turnover(transactions):
    """由当日成交额反推合约乘数：mult = 成交额 / (成交价 × 手数)。

    这是最精确的来源——成交额由券商按合约规格直接算出，比任何推算都可靠。
    """
    out = {}
    for t in transactions:
        price, lots, turnover = t["price"], t["lots"], t["turnover"]
        if price and lots and turnover:
            m = turnover / (price * lots)
            r = int(round(m))
            if r > 0 and abs(m - r) < 0.02:
                out.setdefault(t["contract"], r)
    return out


def _mtm_derived(delta, mtm, lots):
    """由盯市盈亏反推乘数：mtm = delta × 手数 × 乘数。返回整数乘数或 None。"""
    if abs(delta) < 1e-9 or abs(mtm) < 1e-9 or not lots:
        return None
    m = abs(mtm) / (abs(delta) * lots)
    r = int(round(m))
    if r > 0 and abs(m - r) < 0.02:
        return r
    return None


def resolve_multiplier(code, contract, avg_open, prev_s, today_s, mtm, lots,
                       turn_mult=None, opened_today=False, warnings=None):
    """返回 (multiplier, basis)。

    basis: known=品种表 / turnover=成交额反推 / prev=昨结反推 / open=开仓价反推。
    """
    warnings = warnings if warnings is not None else []
    known = known_multiplier(code, contract)
    tm = (turn_mult or {}).get(contract)

    # 1) 当日成交额反推——最精确（券商自己的成交额 = 成交价 × 手数 × 乘数）
    if tm:
        if known and tm != known:
            warnings.append(
                f"{contract}: 成交额反推乘数 {tm} 与品种表 {code}={known} 不一致，采用成交额口径")
            return tm, "turnover"
        return tm, "turnover"

    # 2) 品种表乘数（合约规格静态值）；持仓未在当日新开时用盯市盈亏交叉校验
    if known:
        if not opened_today:
            m = _mtm_derived(prev_s - today_s, mtm, lots)
            if m and m != known:
                warnings.append(
                    f"{contract}: 盯市反推乘数 {m} 与品种表 {code}={known} 不一致，采用盯市口径")
                return m, "prev"
        return known, "known"

    # 3) 未收录品种：用盯市盈亏兜底反推（部分跨日仓口径混合，仅在无法解析时使用）
    cands = {}
    for basis, delta in (("prev", prev_s - today_s), ("open", avg_open - today_s)):
        m = _mtm_derived(delta, mtm, lots)
        if m and m in VALID_MULTS:
            cands.setdefault(basis, m)
    if not cands:
        warnings.append(f"{contract}({code}): 无法反推合约乘数，浮盈浮亏不可计算")
        return None, None
    if len(set(cands.values())) == 1:
        b = next(iter(cands))
        return cands[b], b
    warnings.append(f"{contract}({code}): 乘数反推有歧义 {cands}，优先采用隔日盯市口径")
    return cands.get("prev", list(cands.values())[0]), "prev"


def parse_positions(text, warnings, turn_mult=None, opened_contracts=None):
    recs = []
    turn_mult = turn_mult or {}
    opened_contracts = opened_contracts or set()
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
        contract = c[3]
        code = contract_code(contract)
        mult, basis = resolve_multiplier(
            code, contract, avg_open, prev_s, today_s, mtm, lots,
            turn_mult=turn_mult, opened_today=contract in opened_contracts,
            warnings=warnings)
        floating = None
        if mult:
            diff = (today_s - avg_open) if direction == "多" else (avg_open - today_s)
            floating = round(diff * lots * mult, 2)
        # 持仓表无日期列：|投资单元|交易编码|品种|合约|买持|买开均价|卖持|卖开均价|昨结|今结|盯市|保证金|投保|多市值|空市值|账号|
        recs.append({
            "product": c[2], "contract": contract, "direction": direction,
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
    turn_mult = mult_from_turnover(rec["transactions"])
    opened_contracts = {t["contract"] for t in rec["transactions"] if t["oc"] == "开"}
    rec["open_positions"] = parse_positions(text, warnings, turn_mult, opened_contracts)
    rec["warnings"] = warnings

    b, p = rec["balance"], rec["pnl"]
    no_mult = [x["contract"] for x in rec["open_positions"] if x["multiplier"] is None]
    rec["derived"] = {
        "net_change": round(b["closing"] - b["opening"] - b["deposit_withdrawal"], 2),
        "fee_total_from_trades": round(sum(t["fee"] for t in rec["transactions"]), 2),
        "realized_total_from_closes": round(sum(x["realized_pnl"] for x in rec["closed_positions"]), 2),
        "mtm_total_from_positions": round(sum(x["mtm_today"] for x in rec["open_positions"]), 2),
        "floating_pnl_total": round(sum(x["floating_pnl_at_settle"] or 0 for x in rec["open_positions"]), 2),
        "positions_without_multiplier": no_mult,
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


def read_trades_rows(csv_dir):
    path = Path(csv_dir) / "trades.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _fmt_date(d):
    if d and len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:]}"
    return d or ""


def _dir_of(bs):
    return "多" if bs == "买" else ("空" if bs == "卖" else bs)


def rebuild_ledger_md(csv_dir, knowledge_base_dir):
    """从 trades.csv 全量重建 开平仓记录.md（幂等）。"""
    rows = read_trades_rows(csv_dir)
    if not rows:
        return None
    # 平仓明细匹配表：
    #   open_map 精确表：(close_date, contract, lots, close_price) -> (open_date, open_price, dir)
    #   agg_map  聚合表：(close_date, contract, close_price) -> 同日同价的多条平仓腿
    #             （成交记录可按手数合并成一笔，平仓明细仍按腿拆分，需聚合后回填）
    open_map = {}
    agg_map = {}
    for f in sorted(Path(csv_dir).glob("gf_settlement_*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for c in rec.get("closed_positions", []):
            open_map[(c["close_date"], c["contract"], c["lots"], c["close_price"])] = \
                (c.get("open_date"), c.get("open_price"), c.get("position_dir", ""))
            agg_map.setdefault(
                (c["close_date"], c["contract"], c["close_price"]), []).append(c)
    # 乘数表（与 KNOWN_MULT 一致，用于全程盈亏验算）
    days = {}
    for r in rows:
        days.setdefault(r["settlement_date"], []).append(r)
    sections = []
    for date in sorted(days):
        # 统一数值类型（CSV 读入均为字符串）
        tlist = []
        for t in days[date]:
            t = dict(t)
            t["lots"] = inum(t["lots"])
            t["price"] = fnum(t["price"])
            t["realized_pnl"] = fnum(t["realized_pnl"])
            t["fee"] = fnum(t["fee"])
            tlist.append(t)
        days[date] = tlist
        lines = [f"## {_fmt_date(date)}", "", "| 方向 | 动作 | 品种 | 合约 | 手数 | 价格 | 开仓日 | 开仓价 | 当日腿盈亏 | 全程盈亏 | 手续费 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        day_full = 0.0
        has_full = False
        for t in tlist:
            key = (t["settlement_date"], t["contract"], t["lots"], fnum(t["price"]))
            od, op, pdir = (open_map.get(key) or (None, None, ""))
            # 成交按手数合并、平仓明细按腿拆分时：按同日同价聚合匹配，开仓价取加权平均
            if od is None:
                legs = agg_map.get(
                    (t["settlement_date"], t["contract"], fnum(t["price"]))) or []
                total = sum(ln["lots"] for ln in legs)
                if legs and total == t["lots"]:
                    od = legs[0].get("open_date")
                    op = round(sum(ln["open_price"] * ln["lots"] for ln in legs) / total, 4)
                    dirs = {ln.get("position_dir") for ln in legs}
                    pdir = dirs.pop() if len(dirs) == 1 else ""
            # 同日开平但平仓明细缺失时：尝试从当日开仓行匹配（方向=与平仓方向相反）
            if od is None and t["oc"] == "平":
                for x in tlist:
                    if x["oc"] == "开" and x["contract"] == t["contract"] and x["lots"] == t["lots"]:
                        od, op = x["settlement_date"], x["price"]
                        pdir = "空" if t["bs"] == "买" else ("多" if t["bs"] == "卖" else "")
                        break
            action = "开仓" if t["oc"] == "开" else "平仓"
            show_dir = pdir if (t["oc"] == "平" and pdir) else _dir_of(t["bs"]) if t["oc"] == "开" else ""
            full = ""
            if t["oc"] == "平" and od and op:
                mult = known_multiplier(contract_code(t["contract"]), t["contract"])
                if mult:
                    opv = fnum(str(op))
                    # 方向以平仓明细 position_dir 为准（买平=空仓，卖平=多仓），bs 只是操作腿
                    if pdir == "空":
                        diff = opv - fnum(t["price"])
                    elif pdir == "多":
                        diff = fnum(t["price"]) - opv
                    else:
                        diff = (opv - fnum(t["price"])) if t["bs"] == "买" else (fnum(t["price"]) - opv)
                    full = f"{diff * t['lots'] * mult:+.0f}"
                    day_full += diff * t['lots'] * mult
                    has_full = True
            lines.append(
                f"| {show_dir} | {action} | {t['product']} | {t['contract']} | {t['lots']} | {t['price']} | "
                f"{_fmt_date(od) if od else '—'} | {op if op else '—'} | {fnum(t['realized_pnl']):+.2f} | {full or '—'} | {fnum(t['fee']):.2f} |"
            )
        if has_full:
            lines += ["", f"当日全程盈亏合计：**{day_full:+.0f} 元**（口径=开仓价→平仓价，供与复盘对照；结账口径见 settlement_summary.csv）"]
        lines += ["", ""]
        sections.append("\n".join(lines))
    md = LEDGER_MD_HEADER + "\n".join(sections)
    out = Path(knowledge_base_dir) / "交易复盘" / "逐笔" / "开平仓记录.md"
    if not out.parent.is_dir():
        # 非本仓库的 csv 目录（如临时测试目录）不得覆盖正式台账
        print(f"[warn] 台账目录不存在，跳过开平仓台账重建：{out}", file=sys.stderr)
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    return out


def update_trades_csv(csv_dir, rec):
    path = Path(csv_dir) / "trades.csv"
    # 已有文件若为旧版（缺 open_date 列），迁移列结构
    existing = []
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            existing = list(reader)
            old_fields = reader.fieldnames or []
    else:
        old_fields = []
    if existing and "open_date" not in old_fields:
        # 旧版迁移：改写为新表头（历史平仓行的 open_date/full_realized_pnl 留空，历史不补）
        for r in existing:
            r.setdefault("open_date", "")
            r.setdefault("full_realized_pnl", "")
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=TRADE_COLUMNS)
            w.writeheader()
            w.writerows(existing)
    seen = {r["trans_no"] for r in existing if r.get("trans_no")}
    # 平仓行回填：从本日平仓明细取开仓日/开仓价，算全程盈亏（适用于新增与已存在的当日行）
    # close_map 精确表（手数一致）；close_agg 聚合表（成交合并手数、平仓明细按腿拆分）
    close_map = {}
    close_agg = {}
    for c in rec["closed_positions"]:
        close_map.setdefault((c["contract"], c["lots"], c["close_price"]), []).append(c)
        close_agg.setdefault((c["contract"], c["close_price"]), []).append(c)
    used_agg = set()

    def fill_close(t):
        lots, price = inum(t["lots"]), fnum(t["price"])
        cands = close_map.get((t["contract"], lots, price), [])
        c = cands.pop(0) if cands else None
        if c:
            t["open_date"] = c.get("open_date", "")
            mult = known_multiplier(contract_code(t["contract"]), t["contract"])
            if mult and c.get("open_price"):
                if c.get("position_dir") == "空":
                    diff = c["open_price"] - price
                else:
                    diff = price - c["open_price"]
                t["full_realized_pnl"] = round(diff * lots * mult, 2)
            return
        # 成交按合并手数记一笔、平仓明细按腿拆分：按同合约同价聚合匹配
        agg_key = (t["contract"], price)
        if agg_key in used_agg:
            return
        legs = close_agg.get(agg_key) or []
        total = sum(ln["lots"] for ln in legs)
        if not legs or total != lots:
            return
        used_agg.add(agg_key)
        t["open_date"] = legs[0].get("open_date", "")
        mult = known_multiplier(contract_code(t["contract"]), t["contract"])
        if mult:
            opv = sum(ln["open_price"] * ln["lots"] for ln in legs) / total
            dirs = {ln.get("position_dir") for ln in legs}
            pdir = dirs.pop() if len(dirs) == 1 else ""
            diff = (opv - price) if pdir == "空" else (price - opv)
            t["full_realized_pnl"] = round(diff * lots * mult, 2)

    # 已存在的当日平仓行也回填（幂等重跑时补上）
    backfilled = False
    for r in existing:
        if r.get("settlement_date") == rec["settlement_date"] and r.get("oc") == "平" and not r.get("open_date"):
            before = dict(r)
            fill_close(r)
            if r != before:
                backfilled = True
    if backfilled:
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=TRADE_COLUMNS)
            w.writeheader()
            w.writerows(existing)

    for t in rec["transactions"]:
        if t["trans_no"] in seen:
            continue
        t["open_date"] = ""
        t["full_realized_pnl"] = ""
        if t["oc"] == "平":
            fill_close(t)
    new = [t for t in rec["transactions"] if t["trans_no"] and t["trans_no"] not in seen]
    if new:
        exists = path.exists()
        with path.open("a", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=TRADE_COLUMNS)
            if not exists:
                w.writeheader()
            for t in new:
                w.writerow({k: t[k] for k in TRADE_COLUMNS})
    # 每次重建 Markdown 台账（幂等）
    # 台账路径由 csv 目录推导（<root>/账户归档/结算单数据 → <root>/交易复盘/逐笔/…），
    # 避免在临时目录跑脚本时误覆盖正式台账
    vault_root = Path(csv_dir).resolve().parent.parent
    ledger = rebuild_ledger_md(csv_dir, vault_root)
    return path, len(new), ledger


STOPS_REGISTRY = Path(__file__).resolve().parent.parent / "references" / "stops.json"


def load_stops_registry():
    """读取止损登记表；缺失/损坏时返回空 dict。"""
    try:
        data = json.loads(STOPS_REGISTRY.read_text(encoding="utf-8"))
        return data.get("stops") or {}
    except Exception:
        return {}


def build_stop_loss_card(rec, stops):
    """构造未平仓持仓止损提醒卡片（Markdown）。"""
    date = _fmt_date(rec["settlement_date"])
    positions = rec["open_positions"]
    if not positions:
        return None
    lines = [
        f"⏰ **持仓止损提醒**（{date} 闭市）",
        "",
        "账户权益 **{:.2f}** ｜ 风险度 **{}%** ｜ 浮盈浮亏 **{:+.2f}**".format(
            rec["balance"]["equity"] or 0, rec["margin"]["risk_degree_pct"],
            rec["derived"]["floating_pnl_total"]),
        "",
        "| 合约 | 方向 | 手数 | 开仓均价 | 今结算 | 闭市浮盈浮亏 | 止损 |",
        "|---|---|---|---|---|---|---|",
    ]
    unconfirmed = []
    for pos in positions:
        c = pos["contract"]
        stop = stops.get(c) or {}
        stop_price = stop.get("stop_price")
        if stop_price:
            # 判断距离触发还有多远
            diff = (fnum(stop_price) - pos["today_settle"]) if pos["direction"] == "多" \
                else (pos["today_settle"] - fnum(stop_price))
            mult = pos.get("multiplier") or 0
            pts = abs(diff)
            risk = round(pts * mult * pos["lots"], 2) if mult else None
            note = stop.get("note", "")
            extra = f"距触发约 {pts:.0f} 点"
            if risk is not None:
                extra += f"（约 {risk:+.0f} 元）"
            else:
                extra += "（金额未知：乘数未解析）"
            cell = f"✅ {stop_price}（{extra}）" + (f" {note}" if note else "")
        else:
            cell = "⚠️ **待人工确认**"
            unconfirmed.append(c)
        fl = pos["floating_pnl_at_settle"]
        fl_s = f"{fl:+.2f}" if fl is not None else "—(乘数未知)"
        lines.append(
            f"| {c} | {pos['direction']} | {pos['lots']} | {pos['avg_open_price']} | "
            f"{pos['today_settle']} | **{fl_s}** | {cell} |")
    lines.append("")
    no_mult = rec["derived"].get("positions_without_multiplier") or []
    if no_mult:
        lines.append(
            f"⚠️ 合约 **{('、'.join(no_mult))}** 未能解析合约乘数，其浮盈浮亏与止损金额未计入上方合计，请人工核对。")
        lines.append("")
    if unconfirmed:
        lines.append(f"⚠️ 以下合约**未登记止损**，请人工确认后补充：{('、'.join(unconfirmed))}")
        lines.append("补充方式：回复「合约号 + 止损价」（例：MA611 3300），将登记到 skill 止损表。")
    else:
        lines.append("✅ 全部持仓均已登记止损。")
    lines.append("")
    lines.append("注：浮盈浮亏=今结算价对开仓均价（结算价口径）；止损单状态结算单无法获取，需人工登记。")
    return "\n".join(lines)


def send_feishu(md_text, bot="星河邮件助手"):
    """调飞书推送脚本发送 Markdown；成功返回 True。"""
    import subprocess
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".md", prefix="gf_stops_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(md_text)
        r = subprocess.run(
            ["/root/GenericAgent/.venv/bin/python", "/root/dsh-feishu-send.py",
             "--bot", bot, "--file", path],
            capture_output=True, text=True, timeout=60)
        ok = r.stdout.strip().startswith("OK")
        if not ok:
            print(f"  [warn] 飞书推送失败: {(r.stdout + r.stderr).strip()[:200]}", file=sys.stderr)
        return ok
    except Exception as e:
        print(f"  [warn] 飞书推送异常: {e}", file=sys.stderr)
        return False
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(description="解析广发期货结算单")
    ap.add_argument("--json", help="Outlook 下载的附件资源 JSON（contentBytes）")
    ap.add_argument("--txt", help="已解码的 UTF-8 结算单文本")
    ap.add_argument("--out-dir", help="输出目录，默认与输入同目录")
    ap.add_argument("--csv-dir", help="汇总 CSV 目录，默认与 --out-dir 相同")
    ap.add_argument("--no-feishu", action="store_true", help="只生成卡片不推送飞书")
    ap.add_argument("--feishu-bot", default="星河邮件助手", help="飞书机器人名")
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
    trades_path, n, ledger = update_trades_csv(csv_dir, rec)
    files["trades_csv"] = str(trades_path)
    if ledger:
        files["ledger_md"] = str(ledger)

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
        fl = pos["floating_pnl_at_settle"]
        fl_s = f"{fl:+.2f}" if fl is not None else "—(乘数未知)"
        print(f"  持仓 {pos['contract']} {pos['direction']} {pos['lots']}手"
              f" 开均价{pos['avg_open_price']} 今结{pos['today_settle']}"
              f" 乘数{pos['multiplier']}({pos['mult_basis'] or '-'}) 当日盯市{pos['mtm_today']:+.2f}"
              f" 浮动{fl_s}")
    for c in d["checks"]:
        print(f"  [{'OK' if c['ok'] else 'FAIL'}] {c['name']}")
    for w in warnings:
        print(f"  [warn] {w}")
    print("输出文件:")
    for k, v in files.items():
        print(f"  {k}: {v}")
    if n:
        print(f"  trades.csv 新增 {n} 条成交")

    # 持仓止损提醒：生成卡片 + 推送飞书（不影响主流程）
    stops = load_stops_registry()
    card = build_stop_loss_card(rec, stops)
    if card:
        print("\n持仓止损提醒卡片:")
        print(card)
        if not args.no_feishu:
            if send_feishu(card, args.feishu_bot):
                print("  飞书推送: OK")
            else:
                print("  飞书推送: FAIL（不影响归档）")
    else:
        print("\n无未平仓持仓，跳过止损提醒。")


if __name__ == "__main__":
    main()
