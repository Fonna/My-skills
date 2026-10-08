# My-skills

个人技能（Skill）仓库。用于集中管理、版本化、备份自己编写或已安装后沉淀的可复用技能，方便在多台机器 / 多个会话间同步，并在 WorkBuddy 等兼容平台使用。

> 远程地址：`git@github.com:Fonna/My-skills.git`　|　默认分支：`main`

---

## 目录结构

每个技能是一个**独立文件夹**，里面至少包含一个 `SKILL.md`。遵循 [agentskills.io](https://agentskills.io) 规范。

```
My-skills/
├── README.md
├── .gitignore
├── chrome-reading-list/         # Chrome 阅读清单导出
│   ├── SKILL.md
│   ├── README.md                 # 使用说明与依赖
│   └── scripts/export_reading_list.py
├── dictation-pdf-generator/      # 一个技能 = 一个文件夹
│   └── SKILL.md                  # 技能主体（必含 frontmatter）
└── <your-skill-name>/
    ├── SKILL.md
    ├── scripts/                  # 可选：脚本
    ├── references/               # 可选：参考资料
    └── assets/                   # 可选：图片 / 模板等资源
```

- 文件夹名用小写中划线（`kebab-case`），如 `dictation-pdf-generator`。
- 技能的核心逻辑全部写在 `SKILL.md` 里，其余文件按需附属。

## SKILL.md 格式

`SKILL.md` 顶部是 YAML frontmatter，其后为正文（Markdown）：

```markdown
---
name: "技能的中文显示名"
description: "一句话说明触发场景与用途，并列出触发词。例如：当用户要求 XX 时触发。触发词：默写本、听写、dictation。"
---

# 技能标题

正文：工作流程、约束、模板、命令等……
```

- `name`：技能的展示名（中文即可）。
- `description`：越具体越好，WorkBuddy 靠它判断何时调用该技能；建议把**触发词**写进去。

## 已有技能

| 文件夹 | 名称 | 用途 |
| --- | --- | --- |
| [chrome-reading-list](chrome-reading-list/README.md) | Chrome 阅读清单导出 | 读取本机 Chrome 的 Reading List / 稍后阅读，导出 Markdown 和可选 JSON，统计已读 / 未读；支持指定 Profile 与 User Data 路径 |
| `dictation-pdf-generator` | 中译英默写本 PDF 生成 | 把单词书 / 词汇表图片转成可打印的一行两列 A4 默写本 PDF |
| `gf-futures-settlement` | 广发期货结算单解析 | 解析 Outlook 广发期货每日结算邮件（GBK 附件）：实际盈亏 / 当日盯市 / 浮盈浮亏三分口径 + 权益勾稽自检，输出结构化 JSON 与累积 CSV（settlement_summary / trades）供账户趋势分析；配套 Outlook 收件箱自动归档规则 |
| `investment-review-pipeline` | 期货复盘与选品流水线 | 5 品种（FG/SA/PTA/MA/JD）信号 + 龙虎榜数据完整性检查与自动补全、全品种波动友好度排名、技术面与龙虎榜 HTML 看板；复盘前必跑 |
| `tencent-server-ops` | 腾讯云服务器运维 | GenericAgent Streamlit / 飞书机器人 / futures_workbench / journal 同步的 systemd 服务形态、日志查看、代理与搜索配置、工具白名单等运维参考 |
| `agnes-image` | Agnes AI 图片生成 | 通过 Agnes AI 网关（`apihub.agnes-ai.com/v1`，OpenAI 兼容）调用 `agnes-image-2.5-flash` 生图：文生图 / 图生图 / 多图合成，产物自动下载到本地；当前限免 `$0/张`。需环境变量 `AGNES_API_KEY`（勿与 `ARK_API_KEY` 混用，Key 禁止贴进对话） |

> 新增技能后，请在此表格补一行。

## 外部优秀 Skill 收藏

不收入库的外部好 Skill（他人维护），记录在 [good-skills.md](good-skills.md)：基础介绍、地址、安装方式、适用平台等。

## 新增一个技能

1. 在仓库根目录新建文件夹：`mkdir <your-skill-name>`。
2. 在其中创建 `SKILL.md`，写好 frontmatter + 正文（参考上面的格式）。
3. 需要的话补充 `scripts/`、`references/`、`assets/`。
4. 提交并推送：

   ```bash
   git add <your-skill-name>
   git commit -m "feat: 新增技能 <your-skill-name>"
   git push origin main
   ```

已有的本地技能也可将整个文件夹复制到仓库根目录，保留 `SKILL.md` 及其引用的脚本、参考资料和资源，再更新上面的技能索引。只归档可复用技能文件，个人导出结果及本地缓存不入库。

## 把技能装到 WorkBuddy 上使用

WorkBuddy 的**用户级技能**目录是：

```
# Windows
C:\Users\<你的用户名>\.workbuddy\skills\

# macOS / Linux
~/.workbuddy/skills/
```

把本仓库里对应的技能文件夹**整体复制**到该目录下即可启用（例如复制 `dictation-pdf-generator/` → `~/.workbuddy/skills/dictation-pdf-generator/`）。重启 / 新开会话后，WorkBuddy 会根据 `description` 自动在合适的场景调用它。

也可通过 WorkBuddy 的「安装技能」流程从本仓库导入。

## 版本管理约定

- 主分支 `main`，提交信息用中文说明变更，可保留 `feat:` / `fix:` / `chore:` 等前缀。
- `.gitignore` 已排除本地 `.workbuddy/`（含本机记忆，不推送到公仓）及系统垃圾文件。
- Python 缓存和 Chrome 阅读清单默认导出文件已排除；自定义导出路径建议放在仓库外。
- 技能内容改动后及时 `commit` + `push`，保持线上为最新。
