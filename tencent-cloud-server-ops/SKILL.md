---
name: tencent-cloud-server-ops
description: 腾讯云服务器的SSH连接、密钥登录、上传下载及运维排障。用于ssh tencent、49.234.23.55上的GenericAgent、定时任务、mihomo代理、端口或服务异常；普通本地开发或其他服务器不触发。
---

# 腾讯云服务器连接与运维

统一处理用户腾讯云主机的连接、文件传输和服务排障。按用户当前任务选择所需流程，不把登录或传输扩展为部署、升级或服务修改。

## 当前服务边界

2026-10-27用户明确确认：服务器已没有OpenClaw。日常巡检、任务定位和修复不再检查或依赖OpenClaw的gateway、cron、通道或工具白名单，不自动安装或恢复它。该状态来自用户确认，本次未远程复核。

GenericAgent、飞书前端、mihomo和期货任务保留为已知服务线索，使用前按实际问题核实运行状态；移除OpenClaw不等于已确认其他服务运行正常。

## 连接与身份

- 首选SSH别名 `tencent`，主机 `49.234.23.55`，用户 `root`。Windows优先使用PowerShell和已安装的OpenSSH。
- 以 `ssh -G tencent` 的实际展开配置为准，仅查看hostname、user、port、identityfile、identitiesonly；不按旧笔记重写别名。
- 本机SSH配置为 `C:\Users\YQN\.ssh\config`。2026-10-27本地检查的IdentityFile为 `C:/Users/YQN/.ssh/tencent_openclaw`；这是本地配置证据，不是远程连通性证明。密钥文件名含openclaw不代表服务器仍安装OpenClaw，不因服务移除而自动重命名或替换密钥。
- 不再固定另一份旧文档中的 `tencent_cloud_ed25519`。若现有别名有效，不生成或替换密钥。
- 连接检查使用 `ssh -o BatchMode=yes -o ConnectTimeout=8 tencent 'printf ok'`。缺少认证时报告原因；需要交互输入则在用户可见终端输入，不要求在聊天粘贴密码。
- 不输出私钥、密码、令牌或完整.env；日志和配置仅摘录本次问题所需的非敏感字段。

## 按任务读取

| 用户任务 | 读取内容 |
|---|---|
| 连接、SSH别名/密钥、上传下载、SHA256核验 | [连接与传输](references/ssh-and-transfers.md) |
| 服务、cron、网络、端口或安全组问题 | [服务器服务与诊断](references/server-diagnostics.md) |
| GenericAgent的Streamlit fragment异常或升级问题 | [Streamlit版本与升级副作用](references/genericagent-streamlit-version.md) |
| mihomo、代理出口、搜索引擎重定向 | [代理与搜索历史](references/proxy-and-search.md) |

只加载当前任务需要的附录。历史记录提供检查线索，不直接证明当前版本、端口暴露、工具授权或故障根因。

## 历史资料

仅当用户明确要求分析旧OpenClaw日志、旧备份或迁移历史时，读取[已下线OpenClaw资料](references/history/openclaw-tool-allowlist.md)。不将其中路径、服务单元、工具配置或修复命令用于当前日常排障。

## 执行原则

- 先检查现状，再定位连接、服务、数据抓取、AI报告或agent工具层，依据日志和复现结果选择修复。
- 用户已给出明确操作、源/目标路径及范围时直接执行，不重复询问；路径不明、覆盖未获授权或需扩大影响范围时先澄清。
- 上传下载前解析并说明完整源/目标路径与覆盖行为；完成后尽可能对比文件大小和SHA256。不要仅凭scp退出成功宣称完整无误。
- 检查或传输不顺便修改服务。配置、升级、重启和手动触发任务按用户授权范围执行，先查看潜在hook及外部副作用。
- 修复后用对应场景验证；仅连接成功不等于业务修复，HTTP状态正常也不等于报告生成成功。失败保留证据，不盲目重复写入或触发任务。
- 用中文说明根因、改动、验证和仍未确认的部分。
