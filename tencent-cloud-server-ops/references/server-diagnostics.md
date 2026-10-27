# 腾讯云专机服务与诊断

2026-10-27用户确认：服务器已没有OpenClaw，本次未登录服务器复核。不再将其列为当前服务，也不以其工具白名单或cron为默认诊断路径。

其余服务线索来自原tencent-server-ops的历史记录，使用前核实现场。

## 主机及服务线索

历史主机为Ubuntu 24.04，公网49.234.23.55、内网10.0.0.3，使用root SSH别名tencent。

| 服务 | systemd单元 | 层级 | 历史端口与部署路径 |
|---|---|---|---|
| GenericAgent | genericagent | system | 8501；/root/GenericAgent |
| GA飞书前端 | genericagent-feishu | system | 飞书WebSocket出站；/root/GenericAgent |
| mihomo代理 | mihomo | system | 127.0.0.1:7890；/etc/mihomo/config.yaml |

表列历史服务为system级，使用普通systemctl/journalctl；若现场部署方式不同，以实际单元为准。

## 根据症状定位

- 连接：使用非交互SSH测试，区分别名、认证、DNS、端口和连接超时。
- 服务：查看对应单元状态和近期日志，必要时用 `ss -lntp` 检查监听地址。只有本机监听不代表公网可达；不能仅据超时认定安全组问题，不顺便开放端口。
- 数据抓取：`/root/futures_workbench/` 的cron与akshare/99qh脚本。检查 `crontab -l`、退出码和日志；这一层不依赖agent的web_search。
- AI报告：`ai_report.py` 的模型接口与报告生成。历史为火山引擎chat.completions文本接口，不把agent搜索权限误当成报告接口依赖。
- Agent工具：检查当前实际运行的GenericAgent及其工具、模型和搜索配置，不套用OpenClaw的profile/alsoAllow配置。
- 代理与搜索：先区分代理连通、出口、站点重定向、浏览器和agent工具，按需读代理附录；不靠换节点掩盖工具授权问题。

定时任务从当前crontab、systemd timers或实际应用调度器查起；已下线服务的旧目录和迁移快照不视为有效任务源。调度器归属不明确时先核实，不把旧OpenClaw任务假定为仍在运行。

## 变更与验证

修复依据现场证据，不根据症状自动锁版本、换搜索引擎或改代理。授权修改前保存相关配置并明确回退点，按实际生效要求重载或重启受影响单元。

GenericAgent有git post-merge hook和upgrade.sh：git pull可能自动安装依赖、重启并恢复中文化补丁；即使是拉取代码也可能是完整升级。先读Streamlit附录，不能把git pull当只读诊断。

诊断不默认经第三方镜像拉生产代码；GitHub连接异常先检查既有代理。原笔记的ghfast.top仅是历史备选，不自动替换用户指定来源。

验证应对应实际问题：服务看单元和日志；网络看目标内容与重定向；代理看实际出口；报告/cron若需手动执行，先核实是否会发消息、重复入库或产生交易等外部效果，再按已授权范围执行。查状态不等于获准触发任务。
