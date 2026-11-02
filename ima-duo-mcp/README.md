# ima-duo 的 Codex 适配版

从本机已安装的 `ima-duo-mcp` 同步而来，为 Codex 提供 ima 知识库内的资料移动能力。原项目是 [zeriehan/ima-duo](https://github.com/zeriehan/ima-duo) 的 Obsidian 插件；本包改为独立 Node.js MCP，不依赖 Obsidian 或 WorkBuddy。

上游版本、参考提交、保留接口和全部适配范围见 [UPSTREAM.md](UPSTREAM.md)，许可证见 [LICENSE](LICENSE)。

## 当前能力

| MCP 工具 | 用途 |
| --- | --- |
| `list_knowledge_bases` | 分页查询 OpenAPI 可访问的知识库，取得真实知识库 ID |
| `list_knowledge` | 分页列出知识库根目录或文件夹内条目，取得资料和文件夹 ID |
| `move_knowledge` | 在同一知识库内移动 1–50 个资料，逐项返回结果 |

不支持跨库移动、移动文件夹、删除、重命名或 Obsidian 同步。可与仓库中的 [ima 官方 MCP 适配器](../ima-mcp/README.md) 同时使用；两者授权独立，移动时使用本服务查询得到的 ID。

## 在另一台 Windows 电脑配置

需要 Node.js 22+、Windows PowerShell 及可用的 ima OpenAPI Client ID / API Key。运行脚本无第三方依赖，不需要 `npm install`。

在 My-skills 仓库根目录打开 PowerShell，先复制技能：

```powershell
$imaCodexDir = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$imaSkillDir = Join-Path $imaCodexDir 'skills\ima-duo-mcp'
if (Test-Path -LiteralPath $imaSkillDir) { throw '目标目录已存在，请先检查和备份已有版本' }
New-Item -ItemType Directory -Force -Path (Join-Path $imaCodexDir 'skills') | Out-Null
Copy-Item -LiteralPath '.\ima-duo-mcp' -Destination $imaSkillDir -Recurse
(Get-Command node).Source
Join-Path $imaSkillDir 'scripts\server.mjs'
```

把最后两行输出的绝对路径分别填入 Codex 的 `config.toml` 中。配置文件在 `$imaCodexDir` 下；保留已有配置，只增加下面的服务段。已有 `[mcp_servers.ima_duo]` 时编辑该段，不重复添加。下面 TOML 的单引号允许直接使用 Windows 反斜杠：

```toml
[mcp_servers.ima_duo]
command = 'C:\Program Files\nodejs\node.exe'
args = ['C:\Users\<Windows用户名>\.codex\skills\ima-duo-mcp\scripts\server.mjs']
```

在同一 PowerShell 窗口执行授权配置：

```powershell
node (Join-Path $imaSkillDir 'scripts\auth.mjs') login
```

在打开的本机页面中，按照链接前往 [ima 官方配置页](https://ima.qq.com/agent-interface)，取得 Client ID / API Key 后填回本机表单，验证并加密保存。此流程是 OpenAPI 凭证配置，不是扫码 OAuth。不要将密钥发到聊天或写入仓库。

如果已配置 `IMA_OPENAPI_APIKEY` 或 `IMA_API_KEY` 环境变量，可以使用本机已验证过的环境变量导入方式：

```powershell
node (Join-Path $imaSkillDir 'scripts\auth.mjs') import-env '<你的 Client ID>'
```

也支持通过 `IMA_OPENAPI_CLIENTID` 或 `IMA_CLIENT_ID` 环境变量提供 Client ID，此时省略最后一个参数。支持读取当前进程及 Windows 用户级环境变量，API Key 不作为命令参数传入。不要单独运行内部 `read-env.ps1`，它的输出仅供父进程私下读取。

验证后重启 Codex 或重新加载 MCP 服务。授权验证只查询一页知识库，不自动移动资料。

## 凭证与检查

```powershell
node (Join-Path $imaSkillDir 'scripts\auth.mjs') status
node (Join-Path $imaSkillDir 'scripts\auth.mjs') check
```

`status` 只检查缓存是否存在，`check` 向 ima 发起一次只读请求确认授权。凭证以 Windows DPAPI CurrentUser 加密保存到 `$imaCodexDir\ima-duo-mcp\credentials.dpapi.json`，与技能目录分离；该缓存不能跨电脑或跨 Windows 用户直接使用。其他电脑复制本包后应重新导入凭证。

本机曾通过环境变量导入完成授权，用户已实测资料移动成功。网页表单修正后未重新完成浏览器全流程验证；若页面配置遇到问题，可使用上面的环境变量导入方式。

## 测试

在本技能目录运行：

```powershell
node --test tests/client.test.mjs tests/store.test.mjs
```

共 10 项单元测试，包括移动部分失败、缺失返回码、网络错误不重试、错误脱敏，以及 Windows 加密存取。测试使用模拟接口和临时凭证，不操作真实知识库。
