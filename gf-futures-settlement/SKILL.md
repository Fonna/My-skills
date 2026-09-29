---
name: gf-futures-settlement
description: 解析广发期货每日交易结算单（Outlook 邮件附件，GBK 编码文本），输出结构化盈亏数据——期初/期末结存与客户权益、实际盈亏（平仓）、浮盈浮亏（持仓按今结算价）、当日盯市盈亏、手续费、保证金占用、可用资金、风险度、成交与持仓明细，并维护 settlement_summary.csv / trades.csv 供账户整体趋势分析。当用户要求：解析广发结算单、查当日盈亏、区分实际亏损与浮盈浮亏、看期货账户权益/手续费/风险度、归集期货交易数据做整体分析，或提到 gfqhjsd@gf.com.cn / 客户号 999081322 / 「广发期货结算单」文件夹时使用。
---

# 广发期货结算单解析

把 Outlook 里的广发期货每日结算邮件（附件 `999081322.txt`，GBK 文本）转成结构化数据。核心脚本：`scripts/parse_gf_settlement.py`（纯 stdlib）。格式细节、列定义与坑见 `references/format.md`——列错位或字段缺失时先读它。

## 工作流

1. **找邮件**：用 outlook MCP 查文件夹「广发期货结算单」（收件箱规则已自动归档；发件人 `gfqhjsd@gf.com.cn`，每日一封）。用 `list-mail-folder-messages`（folderId 必填）或 `list-mail-messages` 的 `$search="from:gfqhjsd@gf.com.cn"`（注意 `$search` 与 `$orderby` 不能同用）。**邮件被移动过 message id 会变**，以当前文件夹列表的 id 为准。
2. **取附件**：`list-mail-attachments`（messageId）拿附件 id；`download-bytes-to-file` 落盘附件 JSON。target 用裸路径 `/me/messages/{message-id}/attachments/{attachment-id}`，**不要加 `/$value`**（会被本地路径校验拦截）。文件名建议 `gf_settlement_<日期>_raw.json`，写入当前会话 workspace。
3. **解析**：
   ```
   $env:PYTHONIOENCODING='utf-8'
   python scripts/parse_gf_settlement.py --json <raw.json> --out-dir <DIR> [--csv-dir <DIR>]
   ```
   也支持 `--txt`（已解码文本）。`--out-dir` 默认输入同目录；`--csv-dir` 默认同 out-dir。脚本 stdout 即中文摘要 + 勾稽校验结果。
4. **回答用户**：基于 stdout 与 `<out-dir>/gf_settlement_<日期>.json`。三个盈亏口径必须分清：**实际盈亏**（已平仓实现）、**当日盯市**（结算单口径的单日持仓盈亏）、**浮盈浮亏**（当前持仓按今结算价对开仓价的累计浮动，脚本按结算单反推乘数后计算）。
5. **长期分析**：`settlement_summary.csv` 按结算日一行（同日重跑幂等覆盖）、`trades.csv` 按成交序号去重追加（UTF-8 BOM，Excel 直接开）。**固定累积目录（2026-09-29 起）**：`--csv-dir D:\Github\Glean_Vault\投资\结算单数据`（鹏哥知识库 git 仓库）；同步动作：知识库 `投资/结算单解析.md` 追加当日摘要节、解码原件放 `素材/YYYY-MM-DD_广发期货结算单.txt`、按库内铁律更新 index.md + log.md。git commit/push 需用户授权。

## 校验与异常

- 脚本内置 4 项勾稽（手续费/平仓盈亏/盯市盈亏/权益），出现 `[FAIL]` 时先怀疑表格解析错位，对照 `references/format.md` 列定义排查。
- 未收录品种乘数无法反推时输出 `[warn]`，该持仓浮动记 0——此时人工从结算单 MTM 反推并补充 `KNOWN_MULT`。
- JSON 里没有 `contentBytes` → 下载的不是附件资源本身，回到第 2 步重下。
- 邮件正文提到附件乱码时用"写字板"打开是给人工的提示，与本 skill 无关（脚本直接按 GBK 解）。
