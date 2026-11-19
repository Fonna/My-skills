# 推荐资源目录

记录值得收藏的外部（非自制）Skill / Skill 合集，以及可配合技能使用的插件与工具项目：来源、基础介绍、安装方式、适用平台与使用备注。新增条目时在索引表加一行，并按下文模板补充详情；类型列注明项目实际形态。

设计工具可先查阅 [前端设计技能选型指南](docs/frontend-design-selection.md)，按实际任务选择 image-to-code、Hallmark、Taste Skill 或 Impeccable。

---

## 索引

| 分类 | 名称 | 来源 | 类型 | 适用平台 | 一句话简介 |
| --- | --- | --- | --- | --- | --- |
| 技能 | duckdb-skills | [duckdb/duckdb-skills](https://github.com/duckdb/duckdb-skills) | Claude Code 插件（含 6 个 skill） | macOS / Linux（Windows 暂不完整支持） | DuckDB 官方出品，把本地/远程数据文件直接变成可 SQL 探索的数据库 |
| 技能 / 插件 | Baoyu Design（宝玉设计） | [JimLiu/baoyu-design](https://github.com/JimLiu/baoyu-design) | Agent 技能集 + 本地编辑器，可通过插件接入 | 本地文件型 Agent（Cursor / Claude Code / Codex 等）、DeepSeek Harness；需 Node.js | 用 AI 生成并可视化修改幻灯片、UI 原型、设计系统、数据仪表盘、动画和白板；混合许可，非全仓 MIT |
| 技能 / 工具 | Impeccable | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | 设计 Skill + 命令集 + 确定性检测引擎，另有浏览器扩展 | Codex、Claude Code、Cursor 等；Windows / macOS / Linux，安装与引擎按平台提供 | 从方案梳理到设计评审、局部修改与质量检查；适合外行逐步参与设计，以及后台、仪表盘等任务型界面 |
| 技能 | Hallmark | [Nutlope/hallmark](https://github.com/Nutlope/hallmark) | 前端设计 Skill + 主题资料 + 静态 / 浏览器检查脚本 | Codex、Claude Code、Cursor、OpenCode；Node 18+ | 按页面用途组织内容，以 50 套主题或自定义方向设计新页面，并审查、改造已有界面 |
| 技能 | Taste Skill | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | 前端设计 Skill + 页面素材与动效 + 浏览器检查脚本 | Codex、Claude Code、Cursor 等；Node 22+，Chrome / Edge / Chromium | 用统一页面系统、首屏布局和素材制作公司 / 产品官网，视觉规范较强，不宜直接套用信息密集后台 |
| 技能 | imagegen-skills / image-to-code | [Leonxlnx/imagegen-skills](https://github.com/Leonxlnx/imagegen-skills) | 开源技能合集中的 image-to-code 技能，主要为设计流程说明 | 能生成图片并编写代码的 Agent，如配置相应工具的 Codex / Claude Code | 先生成分章节设计图，再分析并实现网页；适合视觉方案先行的官网、品牌页与作品集 |
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

## Impeccable

- **地址**：[pbakaus/impeccable](https://github.com/pbakaus/impeccable)
- **官网 / 文档**：[impeccable.style](https://impeccable.style/) / [官方文档](https://impeccable.style/docs/)
- **作者 / 维护方**：Paul Bakaus（pbakaus）。
- **协议**：Apache-2.0；二次分发时核对 LICENSE、NOTICE 及第三方组件许可。
- **形态**：面向编程 Agent 的设计技能与命令集，配有确定性反模式检测引擎、CLI、编辑 hook，以及浏览器扩展与 Live Mode；不是独立 BI 平台或无代码数据应用。
- **核查记录**：2026-11-19，仓库声明版本 4.10.0。已阅读 README、技能正文、Operate、shape、critique 等说明；初次登记为文档与规则调研，随后完成下述本机安装与检测验证，尚未做真实业务页面的设计效果对比。

### 基础介绍

把设计工作拆成可以逐步指定的动作：先澄清用途和约束，再形成方案、实现、评审和打磨。`init` 将产品背景记录到 `PRODUCT.md`，`document` 将已有视觉系统记录到 `DESIGN.md`，后续工作复用这些上下文。用户不需要先给出完整规格或 CSS 参数，可以从使用者、问题和最终目的开始讨论。

项目按页面用途区分 Persuade（说服与转化）、Operate（完成任务）、Read（理解内容）、Experience（体验作品）。同一产品的官网与后台可以采用不同模式；客户价值、经营分析、管理后台等优先考虑 Operate，强调可扫描性、熟悉的操作、一致性和必要的信息密度，不把官网式整屏展示套到工作台上。

### 擅长与适用场景

| 擅长的部分 | 对应能力 | 适用场景与选择理由 |
| --- | --- | --- |
| 从模糊目的形成可实施方案 | `shape` 讨论使用者、任务、内容、状态与边界，形成设计简报后停止，不写代码 | 知道“想帮助负责人判断客户价值”，但尚未确定信息层级、布局与操作路径；适合设计外行参与决策 |
| 解释已有页面为什么不好用 | `critique` 是设计评审，给出理由、优先级和需要保留的优点，本身不修改页面 | 初稿显得混乱、不知从何改起，或需要先判断问题再决定是否重设计 |
| 优化任务型界面 | Operate 模式覆盖表格、筛选、导航、组件状态、响应式结构和克制动效 | 客户价值页面、经营看板、管理后台、工具、设置、表单，优先任务效率与一致性 |
| 有针对性的局部迭代 | `layout` 调整布局，`typeset` 调整文字层级，`distill` 减少复杂度，`clarify` 改善界面文案，`polish` 做最后打磨 | 已有可用页面，希望指出具体范围逐步改善，而非每次推翻整页 |
| 检查实现质量与异常状态 | `audit` 检查无障碍、性能、响应式等；`harden` 处理错误、国际化和边界情况；`adapt` 适配设备 | 初稿能看但尚不适合交付，需要补充加载、空数据、长文本、错误反馈及移动端行为 |
| 在浏览器里比较方案 | Live Mode 选择元素并生成多个变体，比较后接受或丢弃，接受的结果写回源码 | 难用语言指定间距与层级，希望看几个实际方案再作选择；该模式仍为 beta |
| 分离机械检测与设计判断 | CLI / hook 提供确定性规则检查，模型负责更广泛的设计与可用性评审 | 在人工评审之外增加重复执行的检查，也可通过 JSON、GitHub 注释或 SARIF 集成到工程流程 |

### 不擅长与使用边界

- **不替代业务指标与数据治理。** 可以协助梳理业务问题，但客户价值公式、客户主体、数据粒度、收入毛利口径、日期、单位、权限与生产接口必须独立核实。设计评审不能证明 SQL 或统计结论正确，也不能把模拟数字当作真实经营事实。
- **设计评分不是用户验证。** `critique` 的启发式分数、模拟使用者视角和检测规则可帮助发现问题，但不等同于真实访谈、可用性测试或业务验收；应看具体理由，而非仅追求高分。
- **检测通过不代表全面合格。** JSX / TSX 等源码扫描主要覆盖模式规则；对比度、小字等渲染问题需要扫描运行中的 URL。规则不可能覆盖全部交互、性能、无障碍或业务行为，仍须项目测试与实际操作。
- **不是全自动无约束建站。** `shape` 刻意停在方案确认阶段；新建页面和重设计需要真实内容、素材及约束。项目自述最擅长已有界面的迭代，新页面也能做，但不能仅凭工具名称假定一次生成即满足业务。
- **不是专门的数据可视化与分析引擎。** 适合改善指标、表格、筛选和详情的呈现；图表类型、聚合公式、多事实表关联及数据更新机制还需数据分析与可视化方案配合，不能代替 BI 数据层。
- **保留品牌与现有逻辑仍需验收。** 使用 `PRODUCT.md`、`DESIGN.md` 和明确范围约束修改；不要把一次局部打磨扩展成全站重设计。模拟评审与浏览器预览不能保证后端、权限和状态转换不受影响。
- **Live Mode 有运行条件与执行边界。** 需要可运行的本地页面或开发服务器，仍为 beta，不适合直接注入生产站点。当前 README 说明：应用暂存文案修改时，如无活跃聊天 Agent 轮询，可能启动本机 Codex / Claude CLI，并关闭其审批与沙箱；需要留在聊天会话中处理时，在启动前设置 `IMPECCABLE_LIVE_COPY_AGENT=chat`，或用 `off` 禁用 Apply。使用前应按实际版本复核该行为。
- **安装、模型与素材不是同一成本。** 确定性检测不需要 LLM 或 API Key，但设计、评审和变体仍依赖宿主 Agent 的模型；生图路径取决于宿主能力。引擎首次运行可能下载二进制文件；不能将“本地项目”理解为模型与素材也完全离线。

### 安装方式与前置条件

安装器需要 Node.js（仓库 npm 包要求 Node 18.19+）；技能运行使用自包含引擎，安装包随附或首次下载，Windows 有对应引擎与 `.cmd` 启动入口。渲染检测需要可用浏览器；完整 Live Mode 还需本地站点可运行。

在目标项目中，仅面向 Codex、仅安装到项目的示例：

```sh
npx impeccable install --providers=codex --scope=project
```

重新加载宿主后点名 `$impeccable init`；按安装器与宿主提示启用所需 hook。仅复制技能目录不会同时安装 hook；安装器接入的 hook 与单次手动扫描应分别验收。更新使用 `npx impeccable update`，更新后确认项目上下文与实际加载版本。

### 客户价值页面的建议用法

1. 明确销售负责人要完成的判断与动作，核实数据范围、指标定义、权限及缺失内容。
2. 用 `init` 记录稳定背景；用 `shape` 讨论客户列表、筛选、趋势、明细及异常状态，形成方案，确认后再实现。
3. 实现时明确采用 Operate 模式，优先沿用现有组件与设计系统；将已核实的最小、典型和最大数据范围纳入布局验证。
4. 有初稿后用 `critique` 评审信息层级、操作路径和解释能力，按优先级选择修改。
5. 按问题使用 `layout`、`clarify`、`distill`、`polish` 等命令；完成后用 `audit` 与运行页面检测核查质量，再做数据与功能验收。

先方案、再实现、后评审是可选的分阶段工作方式，不要求每个小任务都执行全部命令。对用户而言，重点是确认“能否帮助我做判断和采取行动”，而不是先掌握配色、字体与 CSS。

### 本机安装与验证

- **记录日期与环境**：2026-11-19，Windows x64、Codex；通过 Codex 的 skill-installer 安装仓库中的 `.agents/skills/impeccable`，全局技能位置为 `C:\Users\YQN\.codex\skills\impeccable`。技能版本 4.10.0，配套引擎 0.1.27。
- **引擎来源与校验**：启动器从 GitHub Release 下载失败后，通过官方 npm 平台包 `@impeccable/cli-windows-x64@0.1.27` 取得同版本引擎，SHA256 与技能内 `engine-checksums.txt` 完全一致，放入技能的 `scripts/bin/windows-x64/`。`engine-probe` 返回 `impeccable-engine 0.1.27`。
- **验证范围**：技能入口、关键参考文档和 Windows 启动器存在；静态扫描与真实浏览器扫描均识别出测试页面的低对比度文字；修正颜色和字号后，浏览器扫描返回空问题列表、退出码 0。此结果证明安装与检测链路可用，不代表真实业务页面、设计评审质量或完整功能已验收。
- **现有相近技能**：`image-to-code` 与 `redesign-existing-projects` 已启用，前者偏先生图再实现网页，后者偏已有页面视觉改造。磁盘上的 `imagegen-frontend-web`、`gpt-taste`、`high-end-visual-design`、`minimalist-ui`、`industrial-brutalist-ui` 对应技能当时已在 Codex 配置中禁用；此次保留全部既有设置。
- **建议分工**：客户价值、经营分析等任务型页面优先明确点名 `$impeccable`，采用 Operate 模式；视觉展示页需要图像方案先行时再点名 `image-to-code`。避免让强制生图流程与任务型界面规则同时主导一个实现。
- **使用入口与尚未验证项**：下一回合可明确点名 `$impeccable`；用 `shape` 先梳理方案，已有页面用 `critique` 先评审。此次安装的是技能与引擎，未配置或验证自动 hook、Live Mode、浏览器扩展，也未向当前项目写入 PRODUCT.md / DESIGN.md。

来源：[README](https://github.com/pbakaus/impeccable#readme)、[版本与安装器要求](https://github.com/pbakaus/impeccable/blob/main/package.json)、[技能正文](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md)、[Operate 规则](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/reference/operate.md)、[shape](https://impeccable.style/docs/shape/)、[critique](https://impeccable.style/docs/critique/)、[Live Mode](https://impeccable.style/docs/live/)。擅长、不擅长及客户价值页面的流程为据此整理的选型建议；本机安装与检测结果仅限上文列出的验证范围。

---

## Hallmark

- **地址**：[Nutlope/hallmark](https://github.com/Nutlope/hallmark)
- **官网**：[usehallmark.com](https://www.usehallmark.com/)
- **作者 / 维护方**：Nutlope；项目说明由 Together AI 制作。
- **协议**：MIT；照片保留各自的 CC0、公有领域、CC BY 或 CC BY-SA 等许可，使用时须核对具体来源与署名要求。
- **形态**：设计 Skill、按需读取的主题与参考资料、Node 脚本；不是独立设计软件或完整业务应用。
- **核查记录**：2026-11-19，仓库声明版本 2.0.0。已阅读 README、技能正文、改造规则和检查器部分源码；未安装技能，未做同题页面效果对比。

### 基础介绍

让 AI 从访客要完成的任务出发决定页面内容与结构，再选择主题或自定义视觉方向。项目提供 50 套主题；主题主要定义字体、颜色、表面与质感，不要求所有页面采用同一种章节顺序。检查规则分为必须满足的 Floor、可说明理由后豁免的 Reflex，以及精修用的 Finish。

### 擅长与适用场景

| 擅长的部分 | 适用场景与选择理由 |
| --- | --- |
| 按任务组织页面 | 预约、订阅、购买、活动、品牌介绍等新页面，避免固定套用“首屏 + 三张卡片 + 评价 + 订阅”的结构 |
| 提供视觉方向并控制常见 AI 痕迹 | 缺少设计起点，但已有受众、目标、素材与品牌约束时，选择主题或自定义方向 |
| 明确区分改造深度 | 完整重设计、保留布局换风格（restyle）、保留系统与布局做局部打磨（polish） |
| 改造前后留痕与检查 | 用 `--before` 记录链接、字段等，用 `--kept` 检查是否丢失，并提供前后截图对照 |
| 静态与多尺寸浏览器检查 | 检查设计 token、焦点、减少动态效果、首屏与溢出等问题；浏览器检查覆盖 320 至 1920 的八种宽度 |

### 不擅长与使用边界

- **不替代业务需求与数据口径设计。** 客户价值、经营分析等页面，仍须先确认使用者、判断任务、指标定义、粒度、日期、单位和数据权限；主题与 lint 不能保证这些内容正确。
- **默认宣传页面规则不能整体照搬后台。** 项目支持组件与 app scope，但数据表、管理后台和复杂表单应明确采用应用场景，保留必要的信息密度、导航与操作，不强行套用首屏和低字数规则。
- **美学规则有立场，并非通用标准。** 对眉题、字距、渐变、卡片嵌套等限制体现项目取向；已有品牌与锁定的 `design.md` 应优先，合理例外须说明。
- **保留元素不等于功能回归通过。** 链接、字段、处理器等存在性检查不能证明接口、权限、状态转换和端到端业务行为正确，仍需项目自己的测试与实际验收。
- **浏览器检查需要额外环境。** 无 Chrome 或 Puppeteer 时只能做静态检查，不能据此声称移动端、对比度和渲染已通过。审查涉及模型判断的部分也不等同于用户研究。

### 安装方式与前置条件

需要 Node 18+。只安装到当前项目且面向 Codex 的示例：

```sh
npx skills add nutlope/hallmark --agent codex
```

需要全局安装时才加 `-g`。浏览器检查另需 Chrome 及可被脚本找到的 Puppeteer；上游给出的安装方式为 `npm i -g puppeteer-core`。在支持技能加载的 Codex 会话中可点名 `$hallmark`；已有页面需明确要求 Hallmark audit 或 redesign。

来源：[README](https://github.com/Nutlope/hallmark#readme)、[SKILL.md](https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/SKILL.md)、[改造规则](https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/references/redesign.md)、[浏览器检查器](https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/scripts/sloplint-render.mjs)。擅长与不擅长的判断为据此整理的选型建议，不是效果实测结论。

---

## Taste Skill

- **地址**：[Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)
- **官网**：[tasteskill.dev](https://tasteskill.dev/)
- **作者 / 维护方**：Leonxlnx。
- **协议**：MIT；照片、品牌图标等第三方素材须另核对许可与署名要求。
- **形态**：当前仓库主要提供一个 `design-taste-frontend` 技能，配有 HTML / CSS / JavaScript 素材及 Node 检查脚本。
- **核查记录**：2026-11-19，仓库声明版本 2.5.1。已阅读 README、技能正文、变更记录和检查器部分源码；未安装技能，未做同题页面效果对比。

### 基础介绍

以统一的起始页面、设计 token、11 种首屏布局、产品 UI 片段、照片和动效，帮助 Agent 制作公司网站。先区分软件、游戏、技术硬件、普通产品、服务和场所，再选择布局与素材；shader 等效果仅用于适合的技术与游戏类场景。

### 擅长与适用场景

| 擅长的部分 | 适用场景与选择理由 |
| --- | --- |
| 素材与页面系统一并提供 | 需要较完整官网初稿，希望减少 AI 从零拼凑样式、图标、图片和 UI 示意片段 |
| 产品与公司展示 | 软件、开发者工具、产品发布、品牌官网、工作室、酒店或咖啡馆等展示页面 |
| 控制视觉表现的一致性 | 希望首屏、内容边缘、按钮、照片和章节节奏采用统一规则的页面 |
| 按行业选择表现手法 | 技术类页面可选择 shader 与滚动场景；场所、普通商品与服务以照片、排版和克制动效为主 |
| 多尺寸浏览器检查与交付迭代 | 检查遮挡、溢出、图片、对比度、点击区域、占位内容等，并记录豁免与遗留问题 |

### 不擅长与使用边界

- **不宜直接作为信息密集 BI 后台的默认规范。** 每章节一至两屏、首屏入场动画、图片下方无说明等强约束偏向展示网站；经营看板、客户列表、复杂表单应优先任务效率、信息密度与现有组件系统。
- **不替代业务规划和数据建模。** 不负责决定客户价值的正式计算口径、数据关联、权限、生产接口或业务状态；必须先核实这些内容再实现界面。
- **规范较强，未必适合已有品牌和布局。** 对设计系统、章节高度、动效及素材文件的约束较细；严格品牌或成熟应用引入前应逐项判断，而非全量套用。
- **示意 UI 与照片不是客户事实。** 素材片段需要改写为真实产品内容；替代照片不能冒充客户的产品、场地或员工。没有素材与证据时，不能编造业绩或客户评价。
- **交付检查结束不等于全部通过。** `gate.mjs` 默认三轮；仍有问题时可输出 `GATE: OPEN` 并结束本轮，须查看遗留 FAIL 与豁免，不能按 PASS 交付。自动检查也不能替代功能测试和实际用户验证。
- **旧教程可能不再适用。** `high-end-visual-design` 等旧技能已迁往 `taste-skill-classics`，生图相关技能迁往 `imagegen-skills`；不要把旧版技能合集当作当前仓库内容。

### 安装方式与前置条件

需要 Node 22+ 及 Chrome、Edge 或 Chromium；非标准位置可设置 `CHROME_PATH`。ffmpeg 为可选项，用于部分照片转换与裁切。配套脚本本身不要求 API Key，Agent 的模型与额外生图仍依赖各自配置。

只安装到当前项目且面向 Codex 的示例：

```sh
npx skills add https://github.com/Leonxlnx/taste-skill --skill design-taste-frontend --agent codex
```

需要全局安装时才加 `-g`。新开支持技能加载的会话后明确点名 `design-taste-frontend`。空目录可从静态 HTML 起步；已有 React / Vue / Svelte / Astro 等项目在其技术栈中整合；当前文档的 Next.js 新建流程采用静态导出，不能由此推断支持完整动态业务后端。

来源：[README](https://github.com/Leonxlnx/taste-skill#readme)、[SKILL.md](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/SKILL.md)、[交付检查器](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/scripts/gate.mjs)、[变更记录](https://github.com/Leonxlnx/taste-skill/blob/main/CHANGELOG.md)。擅长与不擅长的判断为据此整理的选型建议，不是效果实测结论。

---

## image-to-code（来自 imagegen-skills）

- **地址**：[Leonxlnx/imagegen-skills](https://github.com/Leonxlnx/imagegen-skills)
- **技能入口**：[skills/image-to-code/SKILL.md](https://github.com/Leonxlnx/imagegen-skills/blob/main/skills/image-to-code/SKILL.md)
- **作者 / 维护方**：Leonxlnx，与 Taste Skill 为同一作者；这些生图相关技能原位于 taste-skill，2026 年 10 月拆分到 imagegen-skills。
- **协议**：MIT；实际使用的图片、字体、模型和第三方素材仍须分别遵守对应授权与服务条款。
- **形态**：社区开源技能，不是 Codex 官方内置技能；imagegen-skills 是仓库名，image-to-code 是其中一个技能名。合集另有 imagegen-frontend-web、imagegen-frontend-mobile 和 brandkit，不应把仓库名当作单个技能的调用名。
- **核查记录**：2026-11-19，已对照上游 README、技能说明与本地副本的流程规则；本地副本已在 Codex 启用，但无可靠安装版本记录，不能确定具体提交或是否经过修改。未做与其他三个项目的同题生成对比。

### 基础介绍

核心流程为：先生成网页设计图片，再逐项分析布局、文字、字体、间距、颜色和组件，最后写代码尽量还原。视觉任务默认先生成图片；Codex 下倾向每个章节单独生成足够大的图片，必要时补充独立细节图，避免多章节挤在一张难以辨认的长图里。

该技能以 AI 自行生成的设计图为主要视觉依据，不能仅凭名称把它当成任意截图自动转换为生产代码的工具。图片是设计参考；实际网页仍需实现组件、布局、响应式和交互。

### 擅长与适用场景

| 擅长的部分 | 适用场景与选择理由 |
| --- | --- |
| 先展示可见方案，再实施 | 内容与主要功能已明确，但用户难以用文字指定风格，希望先看设计图片再确定方向 |
| 强视觉表现的网页 | 品牌官网、个人作品集、产品展示、活动宣传、编辑式页面、强调首屏的落地页 |
| 按图分析与还原 | 需要从设计图中提取排版、留白、颜色、按钮与组件关系，并约束编码时的随意改动 |
| 分章节处理复杂视觉稿 | 多章节官网需要独立、清晰的设计参考，避免一次生成太多内容导致文字和细节无法分析 |
| 保持一套视觉语言 | 首屏、章节、按钮和素材需要延续同一套方向，同时减少重复模板和无意义嵌套容器 |

### 不擅长与使用边界

- **不能替代需求梳理。** 先生成图片不等于已经确定使用者、判断任务、内容优先级和验收标准。目的不明时，先讨论或采用 Impeccable 的 shape，避免把不合理结构固化成视觉稿。
- **不宜作为信息密集业务后台的默认流程。** 强调留白、首屏简洁和图像表现；客户列表、复杂筛选、表格、工作台应优先操作效率与合理密度，需要明确约束，不能照搬官网构图。
- **静态设计图不能覆盖全部交互。** 加载、空数据、错误、权限、分页、排序、筛选、长文本与极端数值等状态需要另行设计、实现和验证。
- **视觉图不提供真实数据与业务逻辑。** 图中出现的数字、客户名、评价或 Logo 不能作为事实依据；正式页面只使用已核实内容，示意数据应明确标记。生图文字也不能直接当作可靠业务文案。
- **还原不是像素级保证。** 字体、图片、断点和浏览器环境都会影响结果；应实际渲染网页并验收，不能只看生成的参考图。
- **时间与成本依赖生图服务。** 分章节、补细节和重新生成可能增加调用；技能本身不附带图片生成模型、额度或独立 API，需要宿主提供生图与代码能力。
- **本地副本没有独立检测器。** 当前本地目录只有 SKILL.md，不能视为同时具备 Hallmark、Taste Skill 或 Impeccable 的检测工具。响应式、无障碍和功能测试需要其他工具或工程流程配合。

### 安装方式与本机状态

仅面向 Codex、安装到当前项目的示例：

```sh
npx skills add https://github.com/Leonxlnx/imagegen-skills --skill image-to-code --agent codex
```

需要全局安装时才加 `-g`。安装命令使用 npx，需要 Node.js；使用技能还须具备实际生图和文件读写能力。安装流程本身不代表生图服务已配置。

本机已存在并启用的目录是 `C:\Users\YQN\.codex\skills\image-to-code-skill`，技能声明名为 image-to-code，调用名为 `$image-to-code`。本次仅记录来源与选型信息，未重装、升级或覆盖该副本。目录名、技能名和仓库名可以不同；不能据此推断本地版本。

来源：[仓库说明](https://github.com/Leonxlnx/imagegen-skills#readme)、[技能规则](https://github.com/Leonxlnx/imagegen-skills/blob/main/skills/image-to-code/SKILL.md)。适用与不适用场景为结合本地规则整理的选型建议，不是效果实测结论。

---

## 四个设计项目的选择建议

| 当前任务 | 选择建议 |
| --- | --- |
| 从最终目的梳理客户价值或经营分析页面 | 先核实业务目标、指标、权限和数据；优先试 Impeccable 的 `shape` 将需求转成界面方案，四个项目都不能代替数据口径核实 |
| 对设计不熟，希望在讨论、评审与修改之间逐步推进 | 优先试 Impeccable；`shape` 先定方案，`critique` 先给建议，再选择局部修改命令 |
| 内容和功能已确定，希望先看视觉图片再实现 | 优先试 image-to-code；适合图像方案先行的官网、品牌展示和作品集 |
| 新页面需要设计方向，且希望结构服从任务 | 优先试 Hallmark；已有品牌先锁定 `design.md` |
| 公司 / 产品官网，需要完整素材、首屏布局和统一视觉表现 | 优先试 Taste Skill |
| 已有页面需要解释问题并逐项迭代 | 优先试 Impeccable 的 `critique` / `audit` 与定向修改；Hallmark 的 audit / restyle / polish 也可按改造深度选择 |
| 信息密集后台、表格与表单 | 优先试 Impeccable 的 Operate 模式；保留现有组件与交互系统，不套整屏官网结构 |
| 希望搭配多个设计技能 | 一次实现选一个主技能，其他仅用于明确范围的审查；避免冲突规范同时主导代码 |

完整对比、阶段选择、客户价值页面示例和搭配边界见 [前端设计技能选型指南](docs/frontend-design-selection.md)。通用顺序：使用场景 → 判断任务 → 指标与数据核实 → 布局草图 → 任务验证 → 视觉实现。用户负责业务目标与取舍，AI 可参与全流程提出方案；外观检查通过不代表业务任务已完成。本机启用与验证情况分别见各项目条目，不能由进入推荐目录推断已经安装或测试。

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
