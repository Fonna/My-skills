---
name: tencent-server-ops
description: 腾讯云服务器（49.234.23.55）运维与排障。当用户提到腾讯云服务器、ssh tencent、openclaw 定时任务报错、GenericAgent/GA 服务异常、代理/mihomo 节点问题、端口/安全组、期货数据 cron、或任何"服务器上跑不了/连不上/抓不到"的场景时使用。即使用户没有明确说"运维"，只要涉及这台服务器的服务、网络、定时任务、配置变更都应触发。
---

# 腾讯云服务器运维排障

这台服务器（49.234.23.55，Ubuntu 24.04）是用户的核心生产环境，跑着 openclaw 定时任务和 GenericAgent 服务。排障是最高频场景，本 skill 把反复验证过的连接方式、排障清单、已知坑固化下来，避免每次从零开始。

## 连接（不要每次问 IP/密钥）

直接用 SSH 别名，已配好：

```bash
ssh tencent
```

- IP: `49.234.23.55`，内网 `10.0.0.3`
- 用户: `root`
- 密钥: `~/.ssh/tencent_openclaw`（ed25519）
- 配置在 `~/.ssh/config` 的 `tencent` Host 段

用户本机是 Windows + Git Bash。服务器上 GitHub 直连不稳，克隆走 `ghfast.top` 镜像。

## 上面的两个核心服务

| 服务 | systemd 单元 | 类型 | 端口 | 部署路径 |
|------|-------------|------|------|---------|
| OpenClaw gateway | `openclaw-gateway` | user 级 | 18789（仅 localhost） | npm 全局包 |
| GenericAgent (GA) | `genericagent` | system 级 | 8501（0.0.0.0，外网可达） | `/root/GenericAgent` |

注意：`openclaw-gateway` 是 **user 级** systemd 服务，查状态要用 `systemctl --user`，不是 `systemctl`。GenericAgent 是 **system 级**，用普通 `systemctl`。

## 标准排障链路

按这个顺序走，不要跳步：

### 1. 连接 + 服务健康
```bash
ssh tencent 'systemctl --user status openclaw-gateway; systemctl status genericagent'
```
看是否 `active (running)`。挂了先看 `journalctl --user -u openclaw-gateway -n 50` 或 `journalctl -u genericagent -n 50`。

### 2. 定位问题层
"抓不到网/行情拿不到"这类描述，先分清是哪一层出问题，**不要急着选方案**：

- **数据抓取层**：`/root/futures_workbench/` 下的 cron 脚本（akshare/99qh 抓取）。查 `crontab -l` 和最近日志，看 RC 是否 0。这一层用的是 akshare/99qh，**不走 web_search**。
- **AI 报告层**：`ai_report.py` 调火山引擎 chat.completions，纯文本接口，**也没有 web_search**。
- **openclaw agent 层**：openclaw 的飞书机器人定时任务（铝市/玻璃纯碱简报），这些 agent 会用 web_search/web_fetch/browser 抓行情新闻。**报错"网都抓不到"多数在这一层。**

openclaw 定时任务配置不在 crontab，在 `/root/.openclaw/cron/`（`jobs.json.migrated` 是迁移前快照，真实状态在 state 目录的 sqlite 里）。

### 3. 诊断根因（给证据链）
定位到层之后，给用户一个**带证据的根因结论**，不要只说"可能是xx"。例如：
- ✅ "tools.profile=coding，alsoAllow 里全是 feishu_ 工具，没有 web_search/web_fetch（贴出 grep 结果），所以 agent 用不了搜索"
- ✅ "Google 把出口 IP 46.38.243.197 拉黑了，搜索被 302 到 /sorry/（贴出 curl 结果）"

### 4. 改配置 → 重启 → 验证
改完配置**一定要重启服务并端到端验证**，不要只改不验。

## 已知坑速查（踩过且验证过的）

按"看到什么症状→查什么"组织。详细诊断步骤见对应 reference 文件。

### 症状：openclaw agent 报"web_search 直接禁用 / web_fetch 全部 404"
→ 读 `references/openclaw-tool-allowlist.md`。根因是 `tools.profile=coding` 不含 web 工具，需加 alsoAllow + 配 tavily provider。

### 症状：GenericAgent 报 StreamlitAPIException（fragment 写外部容器）
→ 读 `references/genericagent-streamlit-version.md`。根因是 streamlit 升到了 1.61+，需降级回 1.55.0 并锁版本。

### 症状：GA 浏览器 Google 搜索打不开
→ 读 `references/proxy-and-search.md`。根因通常是出口 IP 被 Google 拉黑；可靠解法是改用 Bing，不是无脑换节点。

### 症状：服务器访问 GitHub/google 慢或超时
→ 服务器在国内，GitHub 直连不稳。克隆走 `ghfast.top`；访问 google 需走 mihomo 代理（127.0.0.1:7890）。

## 端到端验证套路

改完任何东西，至少跑一个验证确认真的好了：

```bash
# 代理出口是否正常
ssh tencent 'curl -s --max-time 10 -x http://127.0.0.1:7890 https://api.ipify.org'  # 看出口 IP
ssh tencent 'curl -s -o /dev/null -w "%{http_code}" --max-time 10 -x http://127.0.0.1:7890 https://www.google.com'  # 期望 200/302

# openclaw 定时任务手动跑一次
ssh tencent 'cd ~/.openclaw && # 跑对应 job，看 RC'

# GenericAgent 服务
ssh tencent 'systemctl status genericagent; curl -s -o /dev/null -w "%{http_code}" http://localhost:8501'
```

## 通用原则

- **先诊断后动手**。用户描述的"报错"经常不在他以为的那一层（如"网抓不到"实际是 agent 工具白名单问题，不是 cron 脚本问题）。先把证据查清楚再改。
- **改配置前看一眼现状**。不要假设配置和上次一样，先 cat/grep 确认当前值。
- **改完必验证**。每次都做到"端到端跑通"才算完，不要只改完就说好了。
- **用中文汇报**。用户偏好中文，诊断结论用中文表格 + 证据。
