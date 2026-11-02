# ima MCP：Codex 的 Windows 接入包

连接 ima 官方 MCP `https://ima.qq.com/mcp`，通过自然语言检索知识库、读取原文，并按需导入网页和文件。Node.js 零 npm 依赖。

**首次授权或重新获取令牌需要 WorkBuddy；授权缓存成功后，使用过程中可以关闭 WorkBuddy。** 运行时 Codex 直接访问 ima MCP，不经过 WorkBuddy 转发业务请求，也不使用 ima Skill/OpenAPI。

```text
首次授权 / 续期：本地脚本 → 同机 WorkBuddy → ima MCP 专用令牌 → Windows DPAPI 加密缓存
日常使用：Codex → 本地 stdio 适配器 → ima 官方 MCP
```

## 在另一台电脑配置

适用于 Windows，需 Node.js 22+、Python 3.11+、Codex。首次授权另需 WorkBuddy 安装、运行、登录并连接个人版 ima。

1. 拉取 `My-skills` 仓库并进入仓库根目录。
2. 打开 WorkBuddy，在 ima 连接器中完成该电脑上的登录和授权。
3. 在 PowerShell 依次运行：

```powershell
# 可选：先预览目标目录，不写入配置。
python .\ima-mcp\scripts\install.py --dry-run

# 复制技能到当前用户的 Codex 技能目录，并登记 MCP 服务 ima。
python .\ima-mcp\scripts\install.py

# 获取并加密保存当前电脑的授权。不会输出令牌。
$imaSkill = Join-Path $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }) 'skills\ima-mcp'
node "$imaSkill\scripts\auth.mjs" login

# 禁止访问 WorkBuddy，只用加密缓存连接 ima，并读取一条资料验证。
node "$imaSkill\scripts\doctor.mjs" --standalone --read-test
```

授权及独立诊断通过后，可以退出 WorkBuddy。重启 Codex 加载 `ima` MCP，试试“列出我在 ima 的知识库”或“查一下 ima 里关于某个主题的资料”。

每台电脑分别授权一次。不复制 `endpoint.json`、WorkBuddy 登录数据或授权缓存；Windows DPAPI 缓存绑定当前电脑上的 Windows 用户，复制到另一台电脑不能直接使用。

## 安装与更新

安装器自动发现 Node.js 路径，复制本目录到 `${CODEX_HOME}/skills/ima-mcp`；未设置 `CODEX_HOME` 时使用 `~/.codex`。MCP 配置引用复制后的目录，仓库移动不会使已安装服务失效。

仅修改 `[mcp_servers.ima]`，写入前通过 TOML 解析验证其他配置不变，并备份已有 `config.toml`。如果已经存在 `ima` 服务，先查看 `codex mcp get ima`，确认替换对象后运行：

```powershell
python .\ima-mcp\scripts\install.py --replace
```

更新仓库后重新运行该命令，再重启 Codex。需要自定义位置时使用 `--codex-home <目录>` 或 `--node <node.exe 路径>`。安装本身不要求 WorkBuddy 正在运行。

其他 MCP 客户端也可使用 stdio 配置：`command` 填本机 `node.exe`，`args` 填完整的 `scripts/bridge.mjs` 路径。不要把示例中某台电脑的绝对路径照搬到另一台电脑。

## 授权、有效期与关闭 WorkBuddy

```powershell
node "$imaSkill\scripts\auth.mjs" status  # 只读本机授权，显示实际有效期
node "$imaSkill\scripts\auth.mjs" login   # 打开并登录 WorkBuddy、连接 ima 后重新取授权
node "$imaSkill\scripts\auth.mjs" clear   # 只删除本机缓存，不撤销远程授权
```

- 缓存为 `${CODEX_HOME}/ima-mcp/auth.dpapi.json`，内容经过 Windows DPAPI CurrentUser 加密；配置文件与仓库不包含真实令牌。`IMA_MCP_AUTH_FILE` 可指定独立缓存路径。
- 有效期来自服务端 `mcp_token_expire_at`，不假定每个账号都有相同期限。即使尚未到期，用户撤销授权或服务端策略变化也可能使其失效。
- 运行时优先使用缓存；缺少有效缓存或遇到 `401` 时，默认尝试通过 WorkBuddy 正常取得授权。WorkBuddy 关闭时失败会给出重新获取授权的提示，不退回 OpenAPI。
- 可在 MCP 的环境变量设置 `IMA_MCP_WORKBUDDY=never`，禁止运行时访问 WorkBuddy；此时重新授权必须显式运行 `auth.mjs login`。
- 切换 ima/WorkBuddy 账号后，执行 `auth.mjs login` 并重启 Codex；缓存不自动跟随账号切换。
- 这仍不是 Codex 独立 OAuth：首次授权及续期依赖 WorkBuddy 的本机 WBIPC 接口，而不是浏览器中的 Codex 授权流程。WorkBuddy 后续版本可能改变该内部接口。

## 诊断

```powershell
node "$imaSkill\scripts\doctor.mjs"                          # 握手与工具发现，必要时尝试 WorkBuddy 授权
node "$imaSkill\scripts\doctor.mjs" --standalone             # 不允许访问 WorkBuddy
node "$imaSkill\scripts\doctor.mjs" --standalone --read-test # 再读取一条个人库内资料，不输出正文
```

没有个人库或没有可读条目时，诊断会报告跳过该读取步骤，不把跳过称作成功读取。遇到 `401` 检查授权；`403` 检查账号或知识库权限。诊断不会创建或导入资料。

## 能力与验证边界

2026-11-02 实测服务 `kb-openapi-mcp/1.0.0` 提供 9 个工具：查库、搜库、列举资料、库内检索、读取正文、列举可添加知识库、批量导入网页、创建上传媒体、添加知识。具体工具、参数及限制以每次连接的 `tools/list` 为准。

已实测知识库读取和检索；文件、网页入库工具已发现，未通过写入测试修改用户资料。当前服务没有创建知识库、重命名、移动或删除已有资料的工具；本包不支持司内版连接器。

## 开发检查

在仓库根目录运行：

```powershell
node --test .\ima-mcp\tests\*.test.mjs
python -m unittest discover -s .\ima-mcp\tests -p 'test_*.py'
```

单元测试使用合成令牌和模拟接口，不需要真实账号。Windows DPAPI 测试仅在 Windows 运行；其他平台不属于本包的支持范围。

移除 MCP：`codex mcp remove ima`。另需移除本机缓存时运行 `auth.mjs clear`；仅移除 MCP 不会撤销 WorkBuddy/ima 远程授权。
