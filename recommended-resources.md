# 推荐资源目录

记录值得收藏的外部（非自制）Skill / Skill 合集，以及可配合技能使用的插件与工具项目：来源、基础介绍、安装方式、适用平台与使用备注。新增条目时在索引表加一行，并按下文模板补充详情；类型列注明项目实际形态。

---

## 索引

| 分类 | 名称 | 来源 | 类型 | 适用平台 | 一句话简介 |
| --- | --- | --- | --- | --- | --- |
| 技能 | duckdb-skills | [duckdb/duckdb-skills](https://github.com/duckdb/duckdb-skills) | Claude Code 插件（含 6 个 skill） | macOS / Linux（Windows 暂不完整支持） | DuckDB 官方出品，把本地/远程数据文件直接变成可 SQL 探索的数据库 |
| 插件 | dsh-workbuddy-connect | [corrinehu/dsh-workbuddy-connect](https://github.com/corrinehu/dsh-workbuddy-connect) | DSH provider 插件（npm 包） | macOS / Windows（Web / Desktop / TUI profile） | 把已登录的 WorkBuddy 桌面 App 模型接入 DeepSeek Harness，国内版与国际版两套分组、账号、积分互不混用 |
| 开发库 | Anime.js | [juliangarnier/anime](https://github.com/juliangarnier/anime) | 前端动画库（非 Skill） | 浏览器；可用于原生 JavaScript / React 等前端项目 | 用时间线、错峰、滚动联动、SVG、文字和拖拽动画制作个人展示、物流流程及交互演示页面 |

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
