# My-skills

个人定制的 WorkBuddy 技能（Skill）仓库。用于集中管理、版本化、备份我自己写的可复用技能，方便在多台机器 / 多个会话间同步。

> 远程地址：`git@github.com:Fonna/My-skills.git`　|　默认分支：`main`

---

## 目录结构

每个技能是一个**独立文件夹**，里面至少包含一个 `SKILL.md`。遵循 [agentskills.io](https://agentskills.io) 规范。

```
My-skills/
├── README.md
├── .gitignore
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
| `dictation-pdf-generator` | 中译英默写本 PDF 生成 | 把单词书 / 词汇表图片转成可打印的一行两列 A4 默写本 PDF |

> 新增技能后，请在此表格补一行。

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

- 主分支 `main`，提交信息用 `feat:` / `fix:` / `chore:` 等前缀，语义清晰即可。
- `.gitignore` 已排除本地 `.workbuddy/`（含本机记忆，不推送到公仓）及系统垃圾文件。
- 技能内容改动后及时 `commit` + `push`，保持线上为最新。
