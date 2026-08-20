# openclaw 工具白名单机制

## 症状
openclaw 的飞书机器人定时任务（铝市/玻璃纯碱简报等）执行时，agent 汇报"web_search 直接禁用，web_fetch 几个 URL 全部 404，行情新闻一条都拿不到"。这看起来像网络问题，实际是**工具白名单配置问题**。

## 根因
openclaw 配置里 `tools.profile = coding`，这个 profile 默认只开放编码相关工具。`alsoAllow` 列表里如果全是 `feishu_` 开头的飞书工具，没有 `web_search` / `web_fetch` / `browser` / HTTP 类工具，agent 就无法联网。

agent 在对话里报"web_search 直接禁用"是 openclaw 的工具权限机制在起作用——不是网络断了，是工具没被授权。

## 配置位置
- 工具配置在 openclaw 的 agent 配置文件里（`/root/.openclaw/` 下的 agent/profile 配置，字段 `tools.profile` 和 `tools.alsoAllow`）
- 定时任务配置在 `/root/.openclaw/cron/`（`jobs.json.migrated` 是迁移前快照，真实运行状态在 state 目录的 sqlite 里）

## 修复步骤（2026-08-07 验证通过）

1. 在 `tools.alsoAllow` 加入 web 工具：
   - `web_search`
   - `web_fetch`
   - `browser`（如需浏览器自动化）

2. 配置搜索 provider：`tools.web.search` 设为 `tavily` provider（需要 tavily API key）。

3. 重启 openclaw gateway 生效：
   ```bash
   systemctl --user restart openclaw-gateway
   ```

4. 端到端验证：手动跑一次定时任务，确认 agent 能搜到行情（如"沪铝 23665"测试通过）。

## 检查命令
```bash
# 看当前 alsoAllow 里有没有 web 工具（grep 应返回非空）
ssh tencent 'cat /root/.openclaw/agents/*.json | grep -E "web_search|web_fetch|browser"'
```

## 注意
- openclaw 升级或换 profile 后可能复现。每次升级后检查 alsoAllow 是否还含 web 工具。
- `openclaw-lark` 插件在 beta 版会加载失败（ERR_PACKAGE_PATH_NOT_EXPORTED for './plugin-sdk'），这是已知的 beta API 兼容问题，不影响 gateway 核心，可忽略。
