# 推荐资源目录

记录值得收藏的外部（非自制）Skill / Skill 合集，以及可配合技能使用的插件与工具项目：来源、基础介绍、安装方式、适用平台与使用备注。新增条目时在索引表加一行，并按下文模板补充详情；类型列注明项目实际形态。

---

## 索引

| 分类 | 名称 | 来源 | 类型 | 适用平台 | 一句话简介 |
| --- | --- | --- | --- | --- | --- |
| 技能 | duckdb-skills | [duckdb/duckdb-skills](https://github.com/duckdb/duckdb-skills) | Claude Code 插件（含 6 个 skill） | macOS / Linux（Windows 暂不完整支持） | DuckDB 官方出品，把本地/远程数据文件直接变成可 SQL 探索的数据库 |
| 技能 / 插件 | Baoyu Design（宝玉设计） | [JimLiu/baoyu-design](https://github.com/JimLiu/baoyu-design) | Agent 技能集 + 本地编辑器，可通过插件接入 | 本地文件型 Agent（Cursor / Claude Code / Codex 等）、DeepSeek Harness；需 Node.js | 用 AI 生成并可视化修改幻灯片、UI 原型、设计系统、数据仪表盘、动画和白板；混合许可，非全仓 MIT |
| 插件 | dsh-workbuddy-connect | [corrinehu/dsh-workbuddy-connect](https://github.com/corrinehu/dsh-workbuddy-connect) | DSH provider 插件（npm 包） | macOS / Windows（Web / Desktop / TUI profile） | 把已登录的 WorkBuddy 桌面 App 模型接入 DeepSeek Harness，国内版与国际版两套分组、账号、积分互不混用 |
| 插件 | text-to-cad | [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad) | CAD 插件（含 Skills、本地建模服务与查看器） | Windows / macOS / Linux，支持 Codex、Claude Code 等 | 用自然语言生成和修改参数化 CAD 零件，支持预览和导出 STEP、STL、3MF、GLB |
| 开发库 | Anime.js | [juliangarnier/anime](https://github.com/juliangarnier/anime) | 前端动画库（非 Skill） | 浏览器；可用于原生 JavaScript / React 等前端项目 | 用时间线、错峰、滚动联动、SVG、文字和拖拽动画制作个人展示、物流流程及交互演示页面 |

---

## Baoyu Design（宝玉设计）

- **地址**：[JimLiu/baoyu-design](https://github.com/JimLiu/baoyu-design)
- **作者/维护方**：Jim Liu（宝玉）；独立社区项目，与 Anthropic 无隶属或背书关系。
- **协议**：混合许可；维护者自有代码为 MIT，来自 Anthropic 的部分不适用 MIT，第三方依赖各按原许可，见下文。
- **形态**：Agent 技能集、预构建的本地编辑器及运行脚本；另提供 DeepSeek Harness 和 ChatGPT / Codex 插件封装。
- **核查记录**：2026-11-11，最新正式版本为 [v2.13.0](https://github.com/JimLiu/baoyu-design/releases/tag/v2.13.0)，新增白板；版本可能继续更新，安装前查看[发布记录](https://github.com/JimLiu/baoyu-design/releases)。本条为文档调研，尚未安装实测。

### 基础介绍

把 Claude Design / claude.ai Artifact 的内容制作流程搬到本地 Agent：描述需求后，由 Agent 写入项目文件并打开对应编辑器；用户可在界面中改文字、拖动元素或标注评论，再交给 Agent 继续修改。产物、评论和历史保存在本地项目文件夹，便于备份和交接。

早期同名的单个 `baoyu-design` 技能（生成自包含 HTML 的 UI 稿和原型）已归档到 `archive/baoyu-design/`；当前主线是下列按产物类型拆分的技能，不应照旧教程默认安装归档版本。

来源：[中文 README](https://github.com/JimLiu/baoyu-design/blob/main/README.zh-CN.md)。

### 核心能力与适用场景

| 技能 | 功能特点 | 适用场景 |
| --- | --- | --- |
| `claude-slides` | 可编辑幻灯片，支持改字、拖动、放映，导出 PDF / HTML / PowerPoint；底层为 `project/deck.json` 和每页 HTML | 业务汇报、经营复盘、方案演示 |
| `claude-design` | 多画板设计画布、交互原型、文案与样式调整；导出 HTML / PDF / PNG / HTML for Figma | 落地页、移动端界面、产品原型 |
| `claude-design-system` | 管理颜色、字体、间距、组件、素材和品牌手册，并供其他设计使用 | 统一报告和产品的视觉规范 |
| `claude-dashboard` | 基于 CSV / TSV / JSON 的图表、指标、表格与筛选；Sources 面板追溯数据行，更换数据文件后重新计算 | 导出数据分析、KPI 展示、周期报告 |
| `claude-motion` | 用代码逐场制作动画，可调整台词、场景时长和样式，导出 MP4 / GIF | 产品介绍、流程讲解、数据故事短片 |
| `motion-director` | 确定影片主题、编写旁白、编排配音和场景；需配合 `claude-motion` | 从业务材料制作叙事影片 |
| `claude-whiteboard` | 可拖动的图形、箭头、便签、表格和手绘；支持评论、共享及版本历史 | 流程梳理、头脑风暴、计划与方案对比 |
| `dataviz` | 图表选型、配色、图例和提示框指南，附配色校验工具，无独立编辑器 | 改善 HTML / SVG / Python 等载体里的图表表达 |

功能来源：[技能总览](https://github.com/JimLiu/baoyu-design/blob/main/README.zh-CN.md#仓库里的技能)、[仪表盘契约](https://github.com/JimLiu/baoyu-design/blob/main/skills/claude-dashboard/SKILL.md)、[幻灯片契约](https://github.com/JimLiu/baoyu-design/blob/main/skills/claude-slides/SKILL.md)。

### 安装方式与前置条件

需要可读写本地文件的 Agent、浏览器及 Node.js。幻灯片、画布和设计系统要求 Node 20+；仪表盘、Motion 和白板要求 Node 22+。编辑器脚本已预构建，通常无需安装项目依赖或自行构建；额外导出工具见下文。

通用技能安装方式（在目标项目中执行；仅安装需要的模块）：

```sh
# 先列出技能，不执行安装
npx skills add JimLiu/baoyu-design --list

# 安装到当前项目：幻灯片和仪表盘
npx skills add JimLiu/baoyu-design --skill claude-slides --skill claude-dashboard
```

安装其他模块时替换 `--skill` 参数；需要全局安装才加 `-g`。安装完成后新开 Agent 会话，让技能重新加载，再明确点名需要的技能。

DeepSeek Harness 桌面版可在 Plugins → Add plugin 按需安装 `dsh-claude-slides`、`dsh-claude-design`、`dsh-claude-design-system`、`dsh-claude-dashboard`、`dsh-claude-motion` 或 `dsh-claude-whiteboard`。Motion 的导演流程还需确保加载 `motion-director`。其他封装方式按[插件安装说明](https://github.com/JimLiu/baoyu-design/blob/main/chatgpt-plugins/README.md)操作；通用安装和 DSH 路径见[项目 README](https://github.com/JimLiu/baoyu-design/blob/main/README.zh-CN.md)。

### 使用时要注意

1. **许可不是全仓 MIT。** [NOTICE.md](https://github.com/JimLiu/baoyu-design/blob/main/NOTICE.md)明确：本地工具及维护者自有代码适用 MIT；取自 Anthropic 的技能说明、参考资料、还原编辑器、`dataviz`、图标字体和归档提示词等不适用 MIT，项目不为这些材料授予许可；归档的 `frontend-design` 技能适用 Apache 2.0，第三方库各按原许可。需要二次分发、打包进产品或商用集成时，应逐项核对授权，不能只看根目录 MIT 文件。
2. **本地编辑器不等于离线模型。** 文件存放本机，但 Agent 是否把内容发送到云端，由所用模型和配置决定；处理公司数据前要核对该配置。项目无额外设计网站订阅要求，也不代表模型调用、生图或配音免费。
3. **模型与设计上下文影响效果。** 上游推荐强模型；提供参考截图、品牌规范、真实代码和清晰的受众、尺寸、导出目标，再生成初稿。不能把示例效果当作所有模型上的质量保证。
4. **编辑器需要本机网络。** 通过 `localhost` / `127.0.0.1` 本地服务器打开，运行环境须允许本地网络访问；写文件和校验能成功，不代表编辑器已能打开。Windows 使用 PowerShell 时采用对应命令语法，不直接照抄 POSIX shell 写法。
5. **评论反馈需要 Agent 在接收。** 评论会保存到本地 `comments.json`；通用技能通过 `comments <root> --wait` 等待时才显示 Send to Agent。没有该入口时可让 Agent 等待评论，或明确要求它读取已保存评论，不能默认标注后就会自动处理。DSH 插件提供自动接收集成。
6. **局域网分享有范围和角色。** `share` / `open --lan` 提供 editor、commenter、viewer 链接，使用明文 HTTP，拿到相应链接的人即可加入；不适合作为公网访问或公司身份权限系统。版本历史有助于恢复修改，但仍应备份；整体 ZIP 可包含评论和历史，交接前核对内容。
7. **导出后仍要验收。** 逐页检查字体、图标、布局和交互；支持 PPTX 不代表所有效果都能原样迁移。HTML for Figma 是供 Chrome 扩展捕捉的页面，不是原生 `.fig` 文件。Motion 导出需要 Chrome，录制产品页面的 `record` 还需要 ffmpeg，配音需自有语音服务或录音；本地白板不提供 claude.ai 的 Ask、光标聊天、朗读和听写助手。
8. **数据来源追溯不代替业务治理。** Dashboard 支持追溯文件数据行，但不能由此认定它具备企业 BI 的权限、指标治理或生产数据库接入能力。实际应用仍要核对数据范围、日期、单位、公式及更新方式。
9. **按版本维护，避免同名技能覆盖。** 保留工作中的产物副本再升级，并核对上游变更。DSH 工作区 `.agents/skills/` 或 `.dsh/skills/` 中的同名技能会优先于插件自带版本，排查时需确认实际加载来源。

上述运行、协作和导出规则以[中文 README](https://github.com/JimLiu/baoyu-design/blob/main/README.zh-CN.md)、[发布记录](https://github.com/JimLiu/baoyu-design/releases)和各模块的 `SKILL.md` 为准；隐私、质量、导出验收及 BI 边界为据此整理的使用建议。

### 备注

优先试用方向：业务数据 CSV → `claude-dashboard`，经营复盘 → `claude-slides`，物流流程或方案梳理 → `claude-whiteboard`。先用非敏感的小样本验证生成、人工修改、评论反馈和目标格式导出，再决定是否用于正式工作。本目录仅登记推荐项目；本次未安装项目或导入第三方技能。

---

## Anime.js

- **地址**：[juliangarnier/anime](https://github.com/juliangarnier/anime)
- **官网 / 文档**：[animejs.com](https://animejs.com/) / [官方文档](https://animejs.com/documentation/)
- **作者/维护方**：Julian Garnier
- **协议**：MIT
- **形态**：JavaScript 动画库，npm 包名为 `animejs`；作为页面开发依赖使用，不是可直接安装到 Agent 技能目录的 Skill。

### 基础介绍

Anime.js 可对 CSS 属性、SVG、DOM 属性和 JavaScript 对象进行动画控制。适合在需要协调多个元素的运动顺序、重叠关系和交互进度时使用，例如个人作品集、物流员工展示、运输流程讲解和数据故事页面。

### 核心能力与适用场景

| 能力 | 用途 |
| --- | --- |
| Animation / Timeline | 控制位移、旋转、缩放等属性，按时间线编排多个动画 |
| Stagger | 让文字、列表、网格或运输节点错峰出现 |
| Events / onScroll | 随滚动触发动画或同步动画进度 |
| SVG | 路线描边、形状变换、物体沿路径移动 |
| Text | 文字拆分与乱码还原效果 |
| Draggable / Easings | 拖拽交互、缓动与弹簧效果 |
| Scope | 管理动画作用域及清理，便于整合组件生命周期 |
| WAAPI / Adapters | 按场景使用 Web Animations API，或通过适配器扩展动画目标 |

能力入口及具体 API 以[官方文档](https://animejs.com/documentation/)为准。

### 安装方式

在目标前端项目目录执行：

```sh
npm install animejs
```

v4 基础用法（页面已有 `.item` 元素）：

```js
import { animate, stagger } from 'animejs';

animate('.item', {
  y: { from: 24, to: 0 },
  opacity: { from: 0, to: 1 },
  duration: 800,
  delay: stagger(100),
  ease: 'outQuint',
});
```

### 适用平台与注意事项

- 页面动效面向浏览器；可整合原生 JavaScript、React 等前端项目。React 接入参考[官方示例](https://animejs.com/documentation/getting-started/using-with-react/)，使用作用域并在组件卸载时清理动画。
- v3 与 v4 API 有差异，使用教程前先核对项目依赖版本；升级时查看[发布记录](https://github.com/juliangarnier/anime/releases)，不要默认小版本更新完全兼容。
- 简单悬停或淡入可直接使用 CSS；复杂时序、路径运动、拖拽和滚动叙事更适合使用此库。按展示目标选择能力，避免为了展示 API 堆叠动效。
- 页面应考虑移动端、键盘操作和减少动态效果偏好；持续循环动画应提供合适的暂停或降级方式。

### 备注

物流员工个人展示页可组合：首屏文字错峰入场、履历滚动时间线、航线 SVG 描边及沿路径运动、示例业绩数字过渡、可拖拽的运输节点。人物与业绩为演示资料时应明确标注。

---

## duckdb-skills

- **地址**：<https://github.com/duckdb/duckdb-skills>
- **作者/维护方**：DuckDB 官方（duckdb org）
- **协议**：MIT　|　**热度**：约 600 stars（2026-10 记录）
- **形态**：Claude Code 插件（plugin），内含 6 个 skill，通过 `/duckdb-skills:<skill-name>` 调用

### 基础介绍

DuckDB 官方发布的 Claude Code 插件，为 Agent 提供「用 DuckDB 探索数据」的全套技能：挂载数据库、跑 SQL、读任意格式数据文件、查官方文档全文检索，甚至翻过往会话日志找回上下文。所有 skill 共享同一份 `state.sql` 会话状态（ATTACH/USE/LOAD、secrets、宏），跨 skill 复用、追加式幂等。

### 包含的 Skills

| Skill | 用途 |
| --- | --- |
| `attach-db` | 挂载 DuckDB 数据库文件，自动探查 schema（表/列/行数）并写会话状态，支持多库叠加挂载 |
| `query` | 对已挂载数据库或临时文件执行 SQL，支持自然语言提问，使用 DuckDB Friendly SQL 方言 |
| `read-file` | 读任意数据文件——CSV / JSON / Parquet / Avro / Excel / spatial / SQLite / Jupyter 等，本地或 S3/GCS/Azure/HTTPS 远程，按扩展名自动识别格式 |
| `duckdb-docs` | 全文检索 DuckDB 与 DuckLake 官方文档、博客（托管索引，HTTPS 直查，可选本地缓存）；SQL 报错时会自动用它排障 |
| `read-memories` | 检索过往 Claude Code 会话日志，找回决策、模式和未完成事项；大结果集自动卸载到临时 DuckDB 文件下钻 |
| `install-duckdb` | 安装/更新 DuckDB 扩展，支持社区扩展 `name@repo` 语法，`--update` 可顺带检查 CLI 版本 |

### 安装方式

Claude Code 内执行（GitHub marketplace 方式，官方市场上架中）：

```
/plugin marketplace add duckdb/duckdb-skills
/plugin install duckdb-skills@duckdb-skills
```

更新：

```
/plugin marketplace update duckdb-skills
/plugin update duckdb-skills@duckdb-skills
```

本地开发/调试：clone 仓库后 `claude --plugin-dir .` 加载。前置条件：需安装 DuckDB CLI（未装时 skill 会引导用 `install-duckdb` 安装）。

### 适用平台与注意事项

- 官方仅在 **macOS / Linux** 测试过；**Windows 尚未完整支持**，部分 shell 命令与路径处理可能异常（对 Windows 为主力机的使用者，建议 WSL 内使用，或等官方兼容性改进）。
- 会话状态文件位置可选：项目内 `.duckdb-skills/state.sql`（可 gitignore）或家目录 `~/.duckdb-skills/<project>/state.sql`。

### 备注

（待补：实际使用感受、与自有工作流的结合点等）

---

## dsh-workbuddy-connect

- **地址**：<https://github.com/corrinehu/dsh-workbuddy-connect>（npm 包名同为 `dsh-workbuddy-connect`）
- **作者/维护方**：corrinehu（社区个人项目）
- **协议**：MIT　|　**热度**：约 530 stars / 60 forks / 225 commits（2026-10 记录；建仓 2026-08-17，更新活跃）
- **形态**：DeepSeek Harness（DSH）的 provider 插件，往 DSH 的模型选择器里注入 WorkBuddy 的模型；不是 Skill，无 SKILL.md，通过 `dsh plugin` 管理

### 基础介绍

把本机已登录的 WorkBuddy / WorkBuddy AI 桌面 App 里的模型直接接进 DSH，零配置使用。国内版显示为「WorkBuddy」分组、国际版显示为「WorkBuddy AI」分组，两版各自只跟随对应 App 的登录状态：只装一版就只出现一组，两版都装则两组并存，退出其一则该组消失；模型、账号、积分互不混用。插件复用 App 的登录态，账号切换自动跟随。

主要能力：

| 能力 | 说明 |
| --- | --- |
| 开箱即用 | 安装启用后无需额外配置，模型直接进选择器 |
| 两版分组并存 | 国内版 / 国际版各自成组，账号与积分隔离；设置里两张卡片分别展示账号与余额 |
| 图片输入 | 多数模型支持对话内直接粘贴/拖入图片（GLM-5.3-Flash、GLM-5.2、DeepSeek-V4 系列等）；纯文字模型（如 GLM-5.1）会明确提示不支持 |
| 推理档位 | WorkBuddy 明确声明的档位直接显示（如 GLM-5.3 / GLM-5.3-Flash 可选 low / high / max）；未声明的模型可在 Web / Desktop 手动检测（会发少量请求、可能消耗积分） |
| 余额速览 | 选中该模型时，输入框底部显示剩余积分；非自动轮询，可手动刷新 |
| 模型显隐 | 插件卡片的「上下文窗口」里勾选要在选择器显示的模型，隐藏配置按登录账号分别保存 |
| 费率与促销徽章 | 模型名后直接显示积分倍率（如 `GLM-5.2 · x0.79`）与促销徽章（限时免费 / 夜间折扣），数据以服务端为准 |
| 企业额度 | 国内版企业账号走企业计费接口，卡片显示周期额度与重置时间（国际版企业账号尚未验证） |

命令行（`desktop` profile 一般由 App 管理，CLI 不可用）：

```sh
dsh plugin --profile web exec dsh-workbuddy-connect status          # 登录状态与剩余积分
dsh plugin --profile web exec dsh-workbuddy-connect doctor          # 诊断
dsh plugin --profile web exec dsh-workbuddy-connect logout          # 清理插件自留凭据副本
# 操作国际版时加 --provider workbuddy-ai
```

### 安装方式

**前置**：本机已安装并登录 WorkBuddy（国内版）或 WorkBuddy AI 桌面 App——插件是复用 App 的登录态，没有桌面端登录态则模型分组不出现。

插件版本必须与 DSH 内核匹配，不匹配会导致 DSH 启动失败：

| DSH 内核 | 推荐插件版 | 注意事项 |
| --- | --- | --- |
| `0.2.0-rc.2` | `0.7.4`（npm latest） | 当前最新线；Windows 注册表发现已修复，勿停留在 0.7.2 |
| `0.2.0-rc.1` | `0.7.0` | 0.7.1 起不再支持 rc.1 |
| `0.1.5` – `0.1.7` | `0.6.5` | 旧内核最终版 |

安装（Web / TUI；Desktop 的 profile 多由 App 管理，官方 Electron 版会拒绝 CLI 的 `--profile desktop`，不要盲用或绕过校验）：

```sh
# Web（按实际内核固定版本）
dsh plugin --profile web add dsh-workbuddy-connect@0.7.4
dsh web

# TUI（需 pnpm 11，终端壳 @deepseek-harness-tui/dsh-tui 需 0.10.0-beta.5+）
dsh plugin --profile dsh-tui add dsh-workbuddy-connect@0.6.5
```

**验证标准**：重启对应界面后，模型选择器出现「WorkBuddy / WorkBuddy AI」分组，并从分组里选一个模型完成一次简短对话且能正常回复，才算安装成功。

### 适用平台与注意事项

- 官方在 **macOS** 的 DSH Web / Desktop / TUI 下验证通过（需 `0.1.5-rc.1`+、Node 22+）。Windows 会依次探测 Local 与 Roaming AppData；WSL 优先从挂载的 Windows 用户目录读凭据。**Linux 不在已验证范围内**：加密桌面凭据的解密程序在 Linux 无法自动发现，需显式指定 `WORKBUDDY_ELECTRON_BIN`（国内版）/ `WORKBUDDY_AI_ELECTRON_BIN`（国际版）指向桌面可执行文件；用户名不一致时用 `WORKBUDDY_AUTH_FILE` / `WORKBUDDY_AI_AUTH_FILE` 指定凭据文件位置。
- **必须与 WorkBuddy 桌面 App 同机使用**：插件的登录态来自本机 App，天然要求两者跑在同一台机器。DSH 跑在远程 Linux 服务器、而 WorkBuddy 装在本地电脑的场景下不可用（服务器上既无 App、也跑不了解密程序）。
- 国际版的模型目录来自 App 界面接口（服务端按 User-Agent 分流），属私有实现，上游改动可能失效；届时插件按「上次成功目录 → 内置目录」降级并在卡片标明来源。国内版目录走官方 CLI 同款接口，不受影响。
- 某版 App 从未登录且无插件自留凭据副本时，该版模型分组不再显示（早期国内版会显示一份内置兜底列表，但选了必然报错）。
- DSH 0.1.7+ / 0.2.0 的设置服务改造后，插件降级为无设置项的 provider：模型、选择器、模型显隐与上下文窗口照常工作，仅「使用上游声明的最大上下文窗口」偏好不再可持久化。
- **依赖不要乱升**：profile 级 `@earendil-works/pi-ai` 必须保持 `^0.87.1`（0.7.2 起由插件自带）；第三方插件管理器的「可更新」提示不校验 peer 约束，照做会引发问题。
- 依赖 WorkBuddy 客户端接口（非官方开放 API），WorkBuddy 更新后插件可能需随之调整。项目仅供个人学习研究使用，与腾讯 / WorkBuddy / DeepSeek 无关联。

### 备注

- 社区有修复 reasoning-effort 的衍生 fork：`@jojoman2024/dsh-workbuddy-connect-patched`（修复上游 `11128` channel-check 错误、hy3 推理不生效问题，并按模型暴露思考档位），同样复用本地登录态，同样受上述同机与平台限制。
- 本机（腾讯云 Linux 服务器）DSH Web profile 已装 `0.7.4` 且版本与内核 `0.2.0-rc.2` 匹配，但服务器无 WorkBuddy 桌面 App，模型分组不会出现——属预期，不影响现有运行。
- （待补：实际使用感受、与自有工作流的结合点等）

---

## text-to-cad

- **地址** [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad)
- **官网 / 文档** [texttocad.dev](https://www.texttocad.dev/) / [官方安装说明](https://github.com/earthtojake/text-to-cad/blob/main/docs/install.md)
- **作者/维护方** earthtojake
- **协议** MIT
- **形态** 面向编程助手的 CAD 插件，包含建模 Skills、本地 MCP 服务和 CAD 查看器。

### 基础介绍

用自然语言描述零件或装配体，助手用 Python 和 build123d 生成可重复运行的建模脚本，再在本地构建并预览。后续可以修改脚本里的尺寸或几何特征，再生成新版本。

### 核心能力与适用场景

| 能力 | 用途 |
| --- | --- |
| 参数化建模与预览 | 创建和修改支架、安装板等机械零件，也可组合成装配体 |
| 文件导出 | 导出 STEP 供其他 CAD 软件打开，导出 STL 或 3MF 供切片，导出 GLB 用于三维展示 |
| 工程图和制造检查 | 生成带尺寸的 PDF 工程图和 2D DXF，也可检查 CNC、钣金或 3D 打印的制造约束 |

### 安装方式

使用支持 `codex plugin add` 的 Codex 版本，先确保系统已安装 `uv`。只给 Codex 安装时，可按项目官方说明添加发布分支和插件。

```sh
codex plugin marketplace add earthtojake/text-to-cad --ref latest
codex plugin add text-to-cad@earthtojake
```

安装后重启 Codex。Claude Code、Cursor 等客户端的安装步骤见[官方安装说明](https://github.com/earthtojake/text-to-cad/blob/main/docs/install.md#app-by-app)。

### 适用平台与注意事项

- 支持 Windows、macOS 和 Linux。首次启动需要联网下载 Python 运行环境和 CAD 内核，之后在本地构建与预览。
- Windows 上如果系统的 `codex` 命令没有 `plugin add`，可使用 Codex 桌面版随附的新版程序。

### 备注

2026-11-04 在 Windows 的 Codex 桌面版实测 `0.10.3`，成功生成并预览一块 80 × 40 × 6 mm 的四孔底板，验证了 STEP 导出。
