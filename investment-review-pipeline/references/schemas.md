# 投资复盘 Pipeline — 参考：路径 / 字段 / 口径红线

本文件为 skill 的详细参考，按需 Load。SKILL.md 只放流程，细节在此。

## 路径与常量

| 项 | 值 |
|---|---|
| 知识库（Obsidian） | `D:\Glean_Vault` |
| 期货数据项目 | `D:\Github\futures_workbench` |
| 5 聚焦品种（代码） | 玻璃 `FG` / 纯碱 `SA` / PTA / 甲醇 `MA` / 鸡蛋 `JD` |
| signals 目录 | `D:\Github\futures_workbench\data\{VARIETY}\signals.json` |
| 机构席位面报告 | `D:\Glean_Vault\投资\复盘_机构席位面_YYYY-MM-DD.md` |
| 跨品种技术面 | `D:\Glean_Vault\投资\跨品种技术面_YYYY-MM-DD.md` |
| 五品种全景 | `D:\Glean_Vault\投资\复盘_五品种全景分析_YYYY-MM-DD.md` |
| 双轨 HTML | `D:\Glean_Vault\素材\YYYY-MM-DD_跨品种技术面快照.html` |
| 龙虎榜 HTML | `D:\Glean_Vault\素材\YYYY-MM-DD_龙虎榜快照.html` |
| 龙虎榜 md | `D:\Glean_Vault\投资\龙虎榜快照_YYYY-MM-DD.md` |
| 持仓记录 | `D:\Glean_Vault\投资\持仓记录.md` |
| 研报信息源 | `D:\Glean_Vault\投资\研报信息源.md`（渠道验证状态 + 品种速查） |
| 操作手册 | `D:\Glean_Vault\AGENTS.md`（§5 会话启动 / §9 HTML 双轨 / 铁律 2·4·5） |

> 鸡蛋 JD = 内资主导品种，无外资维度；其余 4 品种有外资（智大领峰）。

## futures_workbench signals.json 字段表

结构：**扁平 dict，field→list**（同一字段按时间顺序存数组，最新值在 `[-1]`）。
取最新值：`d.get('close')[-1]`。None 值格式化前先渲染成 `—`。

| 字段 | 含义 | 复盘用法 |
|---|---|---|
| `contract_code` | 主力合约代码 | 确认看的是哪期 |
| `fetch_date` | 数据日期 | **新鲜度判断唯一依据**（与今天比对） |
| `close` | 收盘价 | 止损区/浮亏计算 |
| `ma20` / `ma60` / `ma120` | 均线 | 趋势与阻力带（如价跌破 ma120 视为下行确认） |
| `rsi14` | RSI | 超买超卖 |
| `pct_5y` | 5 年分位(%) | 极值超卖（SA 0.25% / FG 6.5%）→ 不追空 |
| `net_long` / `net_short` | 龙虎榜净多/净空 | 99qh 源，与口述席位**不同源** |
| `trend` | 趋势标签 | 「强多/多/震荡/空/强空」；做空需等翻空 |
| `regime` / `regime_action` / `regime_direction` | 风控状态 | 如「清仓报警」 |
| `open_interest` | 持仓量 | 资金热度 |
| `inventory_t` | 仓单库存 | ⚠️ 与「港口社库」非同一指标（见口径红线） |

`scripts/check_freshness.py` 调用示例（在 futures_workbench 根目录跑）：

```bash
cd D:\Github\futures_workbench
C:\Users\Pang\.workbuddy\binaries\python\versions\3.13.12\python.exe \
  C:\Users\Pang\.workbuddy\skills\investment-review-pipeline\scripts\check_freshness.py \
  --data-dir data --varieties FG SA PTA MA JD --today 2026-07-23
```

脚本输出每品种 `fetch_date` 与今天的偏差；全 0 偏差 = 全新鲜。

## 龙虎榜 `position_ranking.csv` 字段表（99qh 源）

落点：`D:\Github\futures_workbench\data\{VARIETY}\position_ranking.csv`，由 `fetch/fetch_99qh.py` 抓取。

结构：**行式 CSV（含 BOM，按 utf-8-sig 读）**，每行一个会员席位。列：

| 字段 | 含义 | 复盘用法 |
|---|---|---|
| `contract` | 主连合约代码（如 jd2609） | 确认看的是哪期；注意 ≠ 远月实盘合约 |
| `side` | `long` / `short` | 区分多/空席位 |
| `isTotal` | `1`=合计行，`0`=会员行 | ⚠️ 分析时剔除合计行（其 netPosition 口径不一致） |
| `rank` | 排名 | TOP5 取前 5 |
| `name` | 期货公司会员名（中信/国君/东证…） | 龙虎榜主体 |
| `position` | 该席位该方向持仓量 | 合计 / TOP5 排序依据 |
| `positionChange` | 较上日持仓变动 | 加仓(+)/减仓(−) |
| `netPosition` / `netPositionChange` | 该会员净持仓及变动 | 会员级，非全市场；全市场净持仓需自算 |

**全市场净持仓（复盘口径）自算**：净持仓 = Σ(多头 position, isTotal=0) − Σ(空头 position, isTotal=0)；净变动 = Σ(多头 positionChange) − Σ(空头 positionChange)。**净空为负、净多为正**（期货惯例，勿反）。

**新鲜度**：CSV 无日期列，以文件 mtime == 今天 判断（见 `check_completeness.py`）。

`scripts/check_completeness.py` 调用示例（在 futures_workbench 根目录跑，不齐可 `--auto-fix` 自动补全）：

```bash
cd D:\Github\futures_workbench
python check_completeness.py --data-dir data --varieties FG SA PTA MA JD --today 2026-07-29
python check_completeness.py --data-dir data --varieties FG SA PTA MA JD --auto-fix   # 缺失/过期则补全并重检
```


## 数据源口径红线（必记）

1. **智大领峰（机构/外资净持仓）= 用户口述源**。模型无法自动抓，必须用户逐品种提供内资/外资净持仓变化（增减幅度：大幅/小幅）。
2. **99qh 龙虎榜（期货公司席位排名）= futures_workbench 抓取源**。方向可能与口述相反，汇报时两者并列，不互相替代。
3. **仓单库存(`inventory_t`) ≠ 港口社库**。用户说「累库」通常指港口社会库存（研报口径）；做空触发以港口库存实数为准，别只看 `inventory_t`。
4. **霍尔木兹(Hormuz) 变量**：PTA、甲醇同受伊朗出口/通航/布油影响。布油破 90+、通航近零 = 成本推涨逻辑活，压制做空。

## 已知坑：akshare `futures_inventory_em` 触发 `py_mini_racer`(V8) 崩溃

- **现象**：`uv run python -m fetch.run_all` 或 `fetch_akshare` 跑到 `futures_inventory_em`（东方财富库存接口，需 JS 算 token）时，`py_mini_racer/mini_racer.dll` 直接 V8 fatal crash，sandbox 内外均崩，**进程退出、数据不落盘**。报错含 `partition_address_space.cc` / `mini_racer.dll` 栈。
- **影响**：仅 `inventory`/`warehouse_snap`（库存/仓单截面）抓不到；`fetch_main`(futures_main_sina) / `fetch_contract`(futures_zh_daily_sina) / `fetch_99qh` **不触发 JS，正常**。
- **绕过法（已验证）**：分两步只抓价+龙虎榜，再 `analyze.run_analyze` 重算：
  ```bash
  cd D:\Github\futures_workbench
  uv run python -m fetch.fetch_akshare SA PTA JD   # 若也崩，改写小脚本只调 futures_main_sina + futures_zh_daily_sina（跳过 inventory/warehouse）
  uv run python -m fetch.fetch_99qh   SA PTA JD   # 龙虎榜正常
  uv run python -m analyze.run_analyze SA PTA JD # 重算 signals.json（fetch_date=今天）
  ```
- **后果**：inventory/warehouse 截面会停留上次成功日（通常差 1 天）。库存变化慢，对结论影响可忽略，在报告 §5 遗漏检查标注「库存截面 N 天滞后待补」即可，勿编造。
- **根因未修**：属 `py_mini_racer` Windows 环境兼容问题，非代码 bug；不要反复重试同一调用（必崩）。

## 研报信息源管理

- 渠道验证状态集中在 `投资/研报信息源.md`：已验证渠道 → 每次必查；待验证 → 仅参考不入结论。
- Stage 2 的「细化」即把新确认的稳定源沉淀进此文件，并可在 skill 内增抓取脚本。
