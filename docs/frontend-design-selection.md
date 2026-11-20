# 前端设计技能选型指南

更新日期：2026-11-20（首次记录：2026-11-19）。用于按实际任务选择 image-to-code、Hallmark、Taste Skill、Impeccable 与 Modern Web Guidance；项目详情、安装方式和本机验证记录见[推荐资源目录](../recommended-resources.md)。

本指南依据项目说明、技能规则和本地安装核查整理，没有开展五个项目同题实施的效果对比。下文的“优先选择”表示流程与场景匹配，不能理解为经过量化测试的质量排名。Modern Web Guidance 主要承担实现阶段的技术指导，前四个项目主要参与设计与界面实现，两类工具可以分工协作。

## 先按需要解决的问题选择

| 现在遇到的问题 | 优先选择 | 原因与边界 |
| --- | --- | --- |
| 只有业务目的，不知道页面该包含什么、如何操作 | Impeccable 的 shape | 先讨论人、任务、内容、状态与约束，形成方案后再实现；业务指标仍须独立核实 |
| 已有初稿，感觉不好用，却说不出具体问题 | Impeccable 的 critique | 解释信息层级、操作路径和一致性问题，给出修改优先级；该命令本身不改页面 |
| 内容与功能已明确，想先看到视觉方案 | image-to-code | 生成设计图片，分析后写代码还原；适合视觉方向需要先看再决定的页面 |
| 新官网需要用途明确、结构合理、风格有区分 | Hallmark | 先按访客任务组织页面，再选择主题或自定义方向，并执行质量检查 |
| 产品发布或公司官网需要完整素材与统一表现 | Taste Skill | 提供布局、照片、UI 片段与动效，并配有浏览器检查；注意强规范对内容的适配 |
| 客户价值、经营看板、管理后台、复杂表单 | Impeccable 的 Operate 模式 | 优先任务效率、密度、熟悉的组件、状态与一致性，避免套用宣传页规则 |
| 已有页面需保留布局换风格或只做局部打磨 | Hallmark 的 restyle / polish，或 Impeccable 的定向修改 | 先确定要保留什么及修改深度，再选一个主流程，不因发现问题便扩大范围 |
| 实现布局、弹窗、表单等，担心沿用旧做法或浏览器不支持 | Modern Web Guidance | 查询现代平台模式、兼容与降级，需适配现有框架和目标浏览器，不重新决定页面用途 |
| 希望扫描全库旧模式再制定现代化方案 | Modern Web Guidance 的 legacy-scan | 只覆盖部分指南对应的确定性旧模式，需逐项核实误报与必要降级；不代替功能测试 |
| 需要核查指标、SQL、数据权限和统计结果 | 独立的数据分析与业务治理流程 | 五者都不是数据治理、指标语义或后端授权工具；页面检测不能证明数据正确 |

## 五个项目的核心区别

| 项目 | 主要依据与工作方式 | 突出能力与推荐场景 | 主要限制 | 检查配套 |
| --- | --- | --- | --- | --- |
| image-to-code | 先生成视觉图，再分析并实现；图片为主要视觉依据 | 分章节参考图、按图还原；作品集、品牌展示、视觉要求高的官网 | 生图增加回合；图片难覆盖全部交互与数据状态，本身不提供完整业务方案 | 本地副本主要为说明文件，需另配检查 |
| Hallmark | 按页面用途、真实素材组织结构，再选择主题或自定义方向 | 风格方向、减少套路、区分改造深度；新官网、预约 / 活动页面、已有页面分级改造 | 美学规则有立场，默认官网规则需按应用场景调整 | 静态 lint 与多尺寸浏览器检查 |
| Taste Skill | 按页面类型选择布局、起始模板与素材系统，再实现 | 素材与视觉一致性；公司官网、产品发布、品牌落地页 | 整屏布局与动效等规范不宜直接套用密集后台 | 一致性、布局、性能、截图及交付检查 |
| Impeccable | 产品目标、使用者任务、设计系统与页面模式驱动；从方案到定向迭代 | 模糊需求梳理、解释问题、局部调整；工作台、仪表盘、表单、设置 | 评审依赖模型与上下文，不替代业务核实或真实用户验证 | 确定性检测引擎与模型设计评审，二者职责不同 |
| Modern Web Guidance | 实现前搜索与读取平台指南，按目标浏览器落实 API、布局、性能和降级策略 | 现代 Web 技术与实施细节；适用于各类页面的具体前端功能，可配合前四者 | 不负责完整业务或视觉方案；新 API 不必强用；扫描仅覆盖部分旧模式 | 指南对照与 legacy-scan；不是完整运行时、性能或无障碍审计 |

这些能力有交集，不是互斥产品分类。Impeccable 也能建新官网，Hallmark 也有 app scope，image-to-code 也会写代码；选择依据是当前最需要哪套工作流程，而非某个工具是否“能生成页面”。

图片生成方面，image-to-code 在视觉任务中要求先生成图片；Hallmark 不是统一必经步骤，Taste Skill 主要使用照片、UI 素材与配套表现；Impeccable 按场景和宿主能力选择，应用界面走代码路径。Modern Web Guidance 不提供生图工作流，不能替代图片生成服务。

## 客户价值页面：建议由 Impeccable 主导

先明确一次具体使用，例如“销售负责人每周找出值得增加投入、需要挽回和需要核查的客户，并安排跟进”。如果实际目标是年度客户结构复盘，页面的信息顺序和内容应随目标变化。

| 阶段 | 应完成的工作 | 工具的角色 | 验收依据 |
| --- | --- | --- | --- |
| 确定目的 | 确认谁使用、何时使用、要判断什么和采取什么动作 | AI 帮助追问和提出方案，用户确认取舍 | 可以用一次具体工作描述用途，避免仅写“展示客户价值” |
| 核实数据 | 明确客户主体、粒度、日期、单位、指标定义、权限与缺口 | 使用已授权的数据与语义流程；设计技能不能代替 | 不编造客户价值得分、潜力、风险阈值或缺失事实 |
| 规划界面 | 讨论筛选、概况、客户名单、变化原因、详情及异常状态 | Impeccable shape，采用 Operate 模式 | 用户能理解方案并指出假设；不必先指定字体或 CSS |
| 实现原型 | 以代表性数据实现核心任务，覆盖长名称、大数值、空值等范围 | Impeccable 配合项目原有技术栈与组件；Modern Web Guidance 按需提供布局、弹窗、表单等实施指导 | 能找到目标客户、理解原因、看到负责人并核查明细；关键行为在目标浏览器可用 |
| 设计评审 | 检查信息优先级、操作路径、密度和状态表达 | Impeccable critique；按优先级选择修改 | 报告有具体证据，优先解决妨碍判断和操作的问题 |
| 打磨与交付 | 定向修改、浏览器检查、数据对账与功能验收 | layout / clarify / distill / polish / audit 按需使用 | 不只看截图，实际验证筛选、排序、分页、权限与错误反馈 |

收入、毛利、增长和逾期等只是可能的维度，必须按实际业务确认。需要看视觉方案时可加入图片探索，但不默认先生成整页精美图片，也不让参考图决定业务事实和操作规则。

## Modern Web Guidance：与主设计流程配合

在客户价值页面中，可以先由 Impeccable 确定客户名单、筛选和详情的操作路径，再由 Modern Web Guidance 查阅具体实现模式。后者不决定客户排名公式，也不因为有新 API 就要求重建现有组件。

| 已确认的需求 | Modern Web Guidance 的角色 | 仍需另外验收 |
| --- | --- | --- |
| 在不同宽度下展示客户表格与筛选区域 | 搜索表格、布局与容器适配指南，选择符合目标浏览器的做法 | 长客户名、列溢出、键盘可达性、排序和分页实际行为 |
| 打开客户详情或确认操作 | 查阅 dialog / popover 等模式、焦点与降级策略 | 弹窗是否合适、关闭与返回流程、屏幕阅读器、业务提交 |
| 列表交互卡顿或图片加载慢 | 查询长任务、调度、资源加载等对应指南 | 测量真实瓶颈，确认处理器、网络、DOM 数量等原因；不能把一条 CSS 或 API 当作通用大数据优化 |
| 全库前端现代化审查 | 用 legacy-scan 获得部分候选，再按规则核实并读取指南 | 必要降级、第三方代码与误报；零发现不等于全面通过 |

普通新增、修复或定向审查采用 search → retrieve → 实现 → 对照检查；legacy-scan 用于用户要求的全库旧模式审查或开放式现代化，不能作为每个组件任务的固定步骤。上游声明扫描规则约覆盖指南目录的 20%。

版本与接入也属于实施约束：当前要求 Node 22+，不稳定或 Origin Trial 特性需显式 opt-in；本地搜索不等于默认无遥测。上游默认收集 Agent 搜索词和指南 ID 等，可用 DISABLE_TELEMETRY=1 关闭。软件与指南分别采用 Apache-2.0 和 CC BY 4.0，二次分发需分别核对。

## 官网与展示页面：按素材和决策方式分流

- **先看样子再决定**：已确认内容和功能，用户希望比较视觉方案，可用 image-to-code 主导。实现后仍需补齐响应式、交互与实际页面验收。
- **需要结构与风格方向**：用 Hallmark 围绕预约、购买、报名、阅读等真实任务组织页面，再选择主题；已有品牌先明确保留内容和设计系统。
- **需要完整官网表现**：用 Taste Skill 组合布局、照片、UI 素材与动效。技术类与普通服务场所的表现规则不同，不能一律增加 shader 或滚动效果。
- **已有页面需渐进改善**：用 Impeccable 先 critique，再针对指定范围修改；或用 Hallmark 明确 restyle / polish 深度，不因选择工具就自动重建全站。
- **具体功能进入代码实现**：无论由哪一个设计技能主导，都可用 Modern Web Guidance 查阅布局、交互、资源加载与兼容策略，保留已确认的内容、设计系统和业务边界。

## 搭配规则与共同边界

1. **同一设计阶段指定一个主技能。** Modern Web Guidance 可在实现阶段作为技术参考，其他工具承担明确范围的审查、素材或局部任务，避免多套强设计规则同时修改同一页面。
2. **切换阶段时带上已确认的决策。** 保留业务目标、真实内容、指标定义、布局约束和设计系统；后一个工具不能重新猜测或擅自推翻。
3. **识别规则冲突。** image-to-code 强调视觉任务先生图；Impeccable 的 Operate 强调任务效率与克制；Taste Skill 的整屏章节偏官网。数据后台应以业务任务与已确认方案为准。
4. **质量检查与业务验收分别完成。** 检测通过不能证明图表聚合、客户归属、SQL、权限或交互逻辑正确；设计评分也不能代替真实用户验证。
5. **真实内容与示意内容明确区分。** 不让图片中的数字、虚构评价、替代照片或 UI 片段冒充客户事实。数据不足时说明缺口，不用视觉包装掩盖。
6. **确认实际执行的检查。** 缺浏览器只能算静态检查；Taste Skill 的 GATE: OPEN 是遗留问题未清零；Impeccable 的自动 hook 与手动扫描是不同接入方式；Modern Web Guidance 的 legacy-scan 只查部分模式，遵循指南不等于浏览器实测通过。
7. **按需使用流程。** 简单局部任务不必依次运行全部命令。生图次数、模型回合和浏览器检查应服务当前的不确定性，不能仅因工具提供就全部执行。

## 本机状态与名称对照

以下保留 2026-11-19 的已有安装核查快照，并于 2026-11-20 增加 Modern Web Guidance 文档调研记录；后续以实际安装与会话加载情况为准。进入推荐清单不代表已经安装。

| 项目 / 上游 | Codex 中的技能名 | 本机状态 | 已验证范围 |
| --- | --- | --- | --- |
| Leonxlnx/imagegen-skills 中的 image-to-code | image-to-code | 原有副本已启用，目录名 image-to-code-skill | 规则与文件检查；具体版本与改动历史未知，无独立检测器 |
| Nutlope/hallmark | hallmark | 本次未安装 | 文档与部分源码调研，未实测页面生成 |
| Leonxlnx/taste-skill | design-taste-frontend | 本次未安装当前项目 | 文档与部分源码调研；磁盘上禁用的旧风格技能不能算当前版已安装 |
| pbakaus/impeccable | impeccable | 已安装技能 4.10.0、Windows 引擎 0.1.27 | 引擎启动、静态与浏览器扫描及修正后复测通过；自动 hook、Live Mode 与真实业务设计未验收 |
| GoogleChrome/modern-web-guidance | modern-web-guidance | 本次未安装；发布仓库声明版本 1.0.1 | 仅文档、技能规则和示例调研，未运行 CLI、兼容或性能实测 |

imagegen-skills 与 taste-skill 为同一作者维护的两个仓库；image-to-code 是前者中的一个技能。仓库名、目录名、技能声明名属于不同层级，不应以本地目录名推断版本或官方来源。

## 来源与后续维护

- [imagegen-skills README](https://github.com/Leonxlnx/imagegen-skills#readme) 与 [image-to-code 规则](https://github.com/Leonxlnx/imagegen-skills/blob/main/skills/image-to-code/SKILL.md)。
- [Hallmark README](https://github.com/Nutlope/hallmark#readme) 与 [改造规则](https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/references/redesign.md)。
- [Taste Skill README](https://github.com/Leonxlnx/taste-skill#readme) 与 [交付检查器](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/scripts/gate.mjs)。
- [Impeccable 技能规则](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md)、[Operate](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/reference/operate.md)、[shape](https://impeccable.style/docs/shape/) 与 [critique](https://impeccable.style/docs/critique/)。
- [Modern Web Guidance 发布仓库](https://github.com/GoogleChrome/modern-web-guidance#readme)、[技能规则](https://github.com/GoogleChrome/modern-web-guidance/blob/main/skills/modern-web-guidance/SKILL.md)、[源码仓库](https://github.com/GoogleChrome/modern-web-guidance-src)与[官方文档](https://developer.chrome.com/docs/modern-web-guidance)。

升级或重新安装时复核命令、版本、许可、浏览器要求与规则变化，并更新本指南和推荐资源中的安装快照。真实业务项目形成可验证经验后，再补充效果与成本记录，避免把文档判断写成实测结论。
