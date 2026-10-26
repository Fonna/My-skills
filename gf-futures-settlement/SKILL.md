---
name: gf-futures-settlement
description: 解析广发期货每日交易结算单（Outlook 邮件附件，GBK 编码文本），输出结构化盈亏数据——期初/期末结存与客户权益、实际盈亏（平仓）、浮盈浮亏（持仓按今结算价）、当日盯市盈亏、手续费、保证金占用、可用资金、风险度、成交与持仓明细，并维护 settlement_summary.csv / trades.csv 供账户整体趋势分析。当用户要求：解析广发结算单、查当日盈亏、区分实际亏损与浮盈浮亏、看期货账户权益/手续费/风险度、归集期货交易数据做整体分析，或提到 gfqhjsd@gf.com.cn / 客户号 999081322 / 「广发期货结算单」文件夹时使用。
---

# 广发期货结算单解析

把 Outlook 里的广发期货每日结算邮件（附件 `999081322.txt`，GBK 文本）转成结构化数据。核心脚本：`scripts/parse_gf_settlement.py`（纯 stdlib）。格式细节、列定义与坑见 `references/format.md`——列错位或字段缺失时先读它。

## 工作流

1. **找邮件**：用 outlook MCP 查文件夹「广发期货结算单」（收件箱规则已自动归档；发件人 `gfqhjsd@gf.com.cn`，每日一封）。用 `list-mail-folder-messages`（folderId 必填）或 `list-mail-messages` 的 `$search="from:gfqhjsd@gf.com.cn"`（注意 `$search` 与 `$orderby` 不能同用）。**邮件被移动过 message id 会变**，以当前文件夹列表的 id 为准。
   - 本机（Linux 服务器）该文件夹 id：`AQMkADAwATM3ZmYAZS1kNzJkLWI1MWQtMDACLTAwCgAuAAADaAlJjd84NEyaoI7ZlqcVnQEAG4MtdwHhjkabfGiB8xE-dgAKAwcgGQAAAA==`；若取不到邮件先用 `list-mail-folders` 重新查（分页 `skip=10`）。
2. **取附件**：`list-mail-attachments`（messageId）拿附件 id；`download-bytes-to-file` 落盘附件 JSON。target 用裸路径 `/me/messages/{message-id}/attachments/{attachment-id}`，**不要加 `/$value`**（会被本地路径校验拦截）。文件名建议 `gf_settlement_<日期>_raw.json`，**直接写到归档目录**（用完删除，勿留在库里）。
3. **解析**：
   ```
   PYTHONIOENCODING=utf-8 python3 scripts/parse_gf_settlement.py --json <raw.json> --out-dir <DIR> [--csv-dir <DIR>]
   ```
   也支持 `--txt`（已解码文本）。`--out-dir` 默认输入同目录；`--csv-dir` 默认同 out-dir。脚本 stdout 即中文摘要 + 勾稽校验结果。
4. **回答用户**：基于 stdout 与 `<out-dir>/gf_settlement_<日期>.json`。三个盈亏口径必须分清：**实际盈亏**（已平仓实现）、**当日盯市**（结算单口径的单日持仓盈亏）、**浮盈浮亏**（当前持仓按今结算价对开仓价的累计浮动，脚本按结算单反推乘数后计算）。
5. **持仓止损提醒**（每日解析后自动执行）：
   - 止损登记表 `references/stops.json`——结算单无法获取止损单状态，须人工确认后登记（键=合约号，值=`stop_price` 触发价 + `note` + `confirmed_date`）。未登记的合约在提醒里标 ⚠️ 待人工确认。
   - 用户回复「合约号 + 止损价」时，用 edit 更新该 JSON 并随库提交。
   - 提醒卡片内容：合约、方向、手数、开仓均价、今结算价、闭市浮盈浮亏、止损状态（含距触发点数/约合金额）。
   - 经飞书「星河邮件助手」推送；推送失败不阻断归档，仅在 stdout 记 `[warn]`。调试时加 `--no-feishu`。
6. **长期分析**：`settlement_summary.csv` 按结算日一行（同日重跑幂等覆盖），`trades.csv` 按成交序号去重追加（UTF-8 BOM；2026-10-16 起新增 `open_date`/`full_realized_pnl` 两列，平仓行自动从平仓明细回填开仓日/开仓价并计算全程盈亏=开仓价→平仓价）。**每日开平仓台账**：脚本自动重建 `/root/Github/Futures_Vault/交易复盘/逐笔/开平仓记录.md`（按日一节，开仓/平仓逐笔分行，同日开平也分行；方向以平仓明细 position_dir 为准，勿手工编辑）。**固定累积目录（随 Futures_Vault 库 git 归档，多机一致）**：`--out-dir /root/Github/Futures_Vault/账户归档/结算单数据 --csv-dir /root/Github/Futures_Vault/账户归档/结算单数据`。解码原件复制到 `/root/Github/Futures_Vault/账户归档/原件/YYYY-MM-DD_广发期货结算单.txt`；摘要维护 `/root/Github/Futures_Vault/交易复盘/账户/结算单解析.md`，更新交易库 `index.md` 和 `log.md`。结算数据随 Futures_Vault 私有仓库 git 同步，不得再写 Glean_Vault/投资/结算单数据或独立的 Futures_Data 目录；Git 提交/推送**遵循用户当前授权**（默认只改工作区，不自动提交）。

## 校验与异常

- 脚本内置 4 项勾稽（手续费/平仓盈亏/盯市盈亏/权益），出现 `[FAIL]` 时先怀疑表格解析错位，对照 `references/format.md` 列定义排查。
- **合约乘数解析顺序**（2026-10-26 修复）：当日成交额反推（`成交额÷成交价÷手数`，最精确）→ 品种表 `KNOWN_MULT` → 盯市盈亏反推兜底。⚠️ 盯市反推公式**必须除以手数**（`乘数=|盯市盈亏|÷(|Δ价|×手数)`），漏除会得到「真实乘数×手数」；且**部分跨日仓**（隔日腿+当日新开腿并存）不服从单一盯市公式，反推必然失败——此时靠成交额或品种表。详见 `references/format.md` 坑位 1–3。
- 乘数仍无法解出时输出 `[warn]`，该持仓浮盈浮亏标「乘数未知」（**不记 0**）并计入 JSON `derived.positions_without_multiplier`，止损卡片同步提示——**脚本不得因此崩溃**（旧版因 `f"{None:+.2f}"` 直接退出码 1，导致飞书提醒未推送）。
- JSON 里没有 `contentBytes` → 下载的不是附件资源本身，回到第 2 步重下。
- 邮件正文提到附件乱码时用"写字板"打开是给人工的提示，与本 skill 无关（脚本直接按 GBK 解）。
- **券商可能漏发或错标结算单**：核对邮件附件的 `日期 Date：` 行与主题日期是否一致（2026-10-21 的邮件实际装的是 20261020 单）。归档前先验附件日期行，不一致按附件实际日期归档并在摘要页注明。
