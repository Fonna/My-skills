# 代理与搜索引擎

## 背景
服务器在国内（腾讯云），访问 Google/GitHub 等需要走代理。代理通过 mihomo（Clash.Meta 后继）实现，订阅来自用户的"一元机场"服务。

## 代理架构
- **mihomo** 作为 systemd 服务运行，监听 `127.0.0.1:7890`（HTTP/SOCKS）
- 配置：`/etc/mihomo/config.yaml`（从用户本地 Clash Verge 提取，已改 `allow-lan: false` 避免公网暴露）
- 全局代理环境变量：`/etc/profile.d/proxy.sh`（新登录 shell 自动 source），含 `http_proxy`/`https_proxy`/`apt` 代理
- 节点选择持久化：mihomo 的 `cache.db` 保存选择器状态，重启不回退
- 二进制位置：服务器 `/usr/local/bin/mihomo`（从本地上传，非 GitHub 下载——因为装代理前服务器连 GitHub 都费劲）

## 关键踩坑：Google 搜索被拦（2026-08-05 验证）

### 现象
GA 的 Chrome（带 `--proxy-server=http://127.0.0.1:7890`）访问 Google 搜索，被 302 重定向到 `www.google.com/sorry/index` 拦截页。

### 根因
出口 IP 是机房 IP（如德国 netcup `46.38.243.197`），Google 会拉黑机房 IP 段。**换节点不能可靠解决**——即使换到日本软银住宅 IP（`45.192.200.254`），Google 搜索仍不稳。

### 可靠解法：改用 Bing
GA 没有独立的 `web_search` 工具，它是靠 system prompt 指示 LLM 用 Chrome 导航搜索引擎。把指示里的 Google 改成 Bing（4 处修改），重启 GA + Chrome 验证即可。Bing 对机房/代理 IP 宽容得多。

### 验证 Google 是否被拦
```bash
ssh tencent 'curl -s -o /dev/null -w "%{http_code}" --max-time 10 -x http://127.0.0.1:7890 "https://www.google.com/search?q=test"'
# 200 = 正常，302 + Location 含 /sorry/ = 被拉黑
```

### 切换 mihomo 节点
```bash
# 看当前出口 IP
ssh tencent 'curl -s --max-time 10 -x http://127.0.0.1:7890 https://api.ipify.org'
# 节点选择通过 mihomo API 或改 config.yaml，cache.db 会持久化
```

## 注意
- 用户本地用的是德国法兰克福节点，但服务器上该节点 IP 被 Google 拉黑。
- 判断节点类型：住宅 IP（如 SoftBank）比机房 IP（如 netcup）更不容易被 Google 拦，但不保证。
- 如果只是访问 GitHub（非 Google），代理通即可，不需要换节点。
