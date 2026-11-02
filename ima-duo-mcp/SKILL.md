---
name: ima-duo-mcp
description: 为 Codex 补充 ima 知识库内资料移动能力，移植自 ima-duo；使用独立的 ima OpenAPI 凭证，不依赖 Obsidian 或 WorkBuddy。适用于明确要求移动、归档 ima 资料或配置该扩展。
---

# ima-duo 的 Codex 扩展

本包是 ima-duo 移动接口的独立适配，不是 Obsidian 插件，也不是 ima 官方 MCP。代码来源、改动和许可证见 [UPSTREAM.md](UPSTREAM.md) 与 [LICENSE](LICENSE)；在其他 Windows 电脑安装和配置时读取 [README.md](README.md)。

先用本服务的 `list_knowledge_bases` 和 `list_knowledge` 获取 OpenAPI 的真实知识库、资料和文件夹 ID，不混用官方 MCP 返回的 ID，不按名称猜测 ID 对应关系。列表按游标分页，单页不是全量。

`move_knowledge` 仅在同一知识库内移动资料；不支持移动文件夹，不提供删除。目标根目录必须显式传 `destination_folder_id: ""`。只有用户明确要求并确定资料和目标时才移动；安装、授权不代表允许测试移动。检查逐项 `outcomes`；部分失败不能报告整批成功。网络超时不自动重试，先核实实际位置。

首次授权运行 `node <本目录>/scripts/auth.mjs login`，在本机页面填写从 https://ima.qq.com/agent-interface 获取的 Client ID/API Key。凭证以 Windows DPAPI CurrentUser 加密存于 `${CODEX_HOME}/ima-duo-mcp/credentials.dpapi.json`，不复制到其他电脑，不写入配置、日志或仓库。

`node <本目录>/scripts/auth.mjs status` 只检查缓存；`check` 发起一次只读查库请求验证授权。凭证失效后重新运行 `login`。本扩展与现有 ima MCP 专用令牌相互独立。

已设置环境变量时，可用 `auth.mjs import-env [ClientID]` 验证并加密导入。支持 `IMA_OPENAPI_APIKEY`/`IMA_API_KEY` 和 `IMA_OPENAPI_CLIENTID`/`IMA_CLIENT_ID`，也读取 Windows 用户级变量。API Key 不作为命令参数传入；不要直接运行内部的 `read-env.ps1`，它的输出仅供父进程私下消费。
