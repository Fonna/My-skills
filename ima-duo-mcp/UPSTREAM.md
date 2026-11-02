# 上游来源与本地改动

## 来源

- 原项目：[zeriehan/ima-duo](https://github.com/zeriehan/ima-duo)，作者 zeriehan。
- 参考版本：0.13.2；参考提交：[54e2c6a9e28d04a2640bc3c2013744e82ddfffef](https://github.com/zeriehan/ima-duo/tree/54e2c6a9e28d04a2640bc3c2013744e82ddfffef)。
- 主要参考文件：[src/ima.ts](https://github.com/zeriehan/ima-duo/blob/54e2c6a9e28d04a2640bc3c2013744e82ddfffef/src/ima.ts)，复用知识库查询、资料列表及 `moveKnowledge` 的 HTTP 请求契约。
- 原项目采用 MIT 许可证，本目录保留原版权声明及 [LICENSE](LICENSE)。

本目录是依据上述接口契约重新实现的 Codex 适配包，不是上游 Obsidian 插件的完整副本，也不是 ima 官方发布的 MCP。`ima-duo-mcp` 是技能目录名，`ima_duo` 是注册到 Codex 的 MCP 服务名。

## 保留和调整的部分

| 部分 | 上游实现 | 本机 Codex 版本 |
| --- | --- | --- |
| 运行方式 | Obsidian 桌面插件，TypeScript | 独立 Node.js stdio MCP，无第三方 npm 依赖 |
| 知识库与资料查询 | 插件内部 OpenAPI 客户端 | `list_knowledge_bases`、`list_knowledge`，保留游标分页，用于获取移动所需真实 ID |
| 移动资料 | `moveKnowledge` 调用 `openapi/wiki/v1/move_knowledge` | `move_knowledge`，仅同库移动资料，根目录必须显式指定；按每个资料的 `ret_code` 判断成功，部分失败反馈为 MCP 工具错误 |
| 授权入口 | 在插件中配置 ima OpenAPI Client ID / API Key | 新增本机网页表单和环境变量导入；执行只读查库验证后保存 |
| 凭证保存 | 插件配置体系 | 新增 Windows DPAPI CurrentUser 加密缓存，存放于技能目录之外；与官方 MCP 的授权独立 |
| 请求与异常 | 供插件同步流程调用 | 限定三个端点、45 秒请求超时、拒绝重定向、错误信息脱敏；不自动重试，移动超时先核实实际位置 |
| Codex 接入 | 无独立 Codex MCP 入口 | 新增 `scripts/server.mjs`、工具描述、`SKILL.md` 及单元测试 |

## 没有移植的上游功能

没有移植 Obsidian 设置界面、笔记库双向同步、自动同步调度、文件上传下载、笔记推送、创建文件夹、重命名，以及同步流程中的回收站整理。上游的回收站整理是移动到回收目录，不等于永久删除；本适配包没有提供删除工具。

## 文件对应关系

- `scripts/client.mjs`：根据上游 `src/ima.ts` 的三个请求契约实现客户端，增加参数校验与逐项移动结果处理。
- `scripts/server.mjs`：新增 MCP JSON-RPC stdio 服务，只暴露上述三个工具。
- `scripts/auth.mjs`：新增本机授权配置页、只读校验、状态检查及环境变量导入命令。
- `scripts/store.mjs`、`scripts/dpapi.ps1`、`scripts/read-env.ps1`：新增 Windows 凭证加密存取和环境变量读取；DPAPI 辅助脚本沿用本机已有 ima MCP 适配器的实现。
- `tests/*.test.mjs`：新增参数边界、部分失败、禁止自动重试、错误脱敏、MCP 初始化及 DPAPI 加密存取测试。
- `SKILL.md`、`README.md`、本文：新增 Codex 调用规则、Windows 配置方式及改动说明。

## 验证状态

2026-11-02：本机已完成授权及只读查询验证；用户已明确反馈，实际移动资料测试成功。已有 10 项单元测试覆盖客户端、MCP 调度和 Windows 凭证存取。移动端点依据上游实现接入，服务端可用范围仍以实际账号及返回结果为准。

本次归档直接同步本机已安装的运行脚本和测试，只补充、更新来源与配置文档；没有添加新业务工具。个人 Client ID、API Key、环境变量值、加密凭证缓存及 Codex 私人配置均不入库。
