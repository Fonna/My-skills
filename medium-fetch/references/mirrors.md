# 镜像回退链与排障

脚本 `scripts/fetch_medium_article.py` 按下表顺序尝试镜像，**第一个拿到有效正文的即采用**；单镜像失败不中断整条链。

| # | 镜像 | 拼法 | 说明 |
| --- | --- | --- | --- |
| 1 | `freedium-mirror.cfd` | `https://freedium-mirror.cfd/<原URL>` | 正文最完整，实际首选 |
| 2 | `freedium.cfd` | `https://freedium.cfd/<原URL>` | 备用域名，常为停放页，自动跳过 |
| 3 | `readmedium.com` | `https://readmedium.com/en/<原URL>` | 需 JS 渲染，通常抓不到正文，兜底 |
| 4 | `direct` | 原 URL 直连 medium.com | 通常被 Cloudflare 拦截，最后尝试 |

换镜像：改 `scripts/fetch_medium_article.py` 顶部的 `MIRRORS` 列表即可，其余代码不用动。

## 失败原因码

`classify_failure()` 判定页面"不像文章"时返回下列原因码之一：

| 原因码 | 判定依据 | 是否值得重试 |
| --- | --- | --- |
| `cloudflare_blocked` | 页面含 `Attention Required` + `cloudflare`，或 `Sorry, you have been blocked` | 否——链上其他镜像也大概率被拦，说明出口 IP 被盯上 |
| `security_check` | `Performing security verification` / `Just a moment...` | 是，等一会儿重试可能过 |
| `mirror_parked` | 页面含 `parkingcrew` / `parklogic` | 否——域名被停放，属正常跳过 |
| `mirror_render_failed` | 页面含 `Failed to render this page` | 否——镜像自身故障 |
| `article_not_found` | 页面含 `article_not_found`，或 SvelteKit 注入 `{html:null}` 载荷 | 否——URL 写错 / 已删 / 付费墙 / 未收录，先核对链接 |
| `page_too_small` | 页面 < 20,000 字节 | 否——多半是错误页 |

**正文长度 > 200 字符**才算有效正文（`MIN_BODY_CHARS`），避免抓到半截页面就当成功。

## 网络与代理

抓取动作交给 `curl` 而不是 Python 的 urllib，原因是：无代理环境下 urllib 不认 `proxychains4`，而本服务器访问 medium.com / freedium 必须走代理。脚本的决策：

- 有任一 `https_proxy` / `HTTP_PROXY` / `ALL_PROXY` 等变量 → 直接 `curl`，由 curl 读环境变量；
- 无代理变量但装了 `proxychains4` → `proxychains4 -q curl ...`；
- 两者都没有 → 直连 `curl`（Cloudflare 大概率拦截）。

其他开关：

- `MEDIUM_FETCH_CURL` — 指定 curl 可执行文件路径
- `--timeout N` — 单镜像超时秒数，默认 90（`curl --max-time`，外层再留 10s 硬杀）

## 正文清洗

清洗分两步，避免误伤正文：

1. **HTML → 文本**：删 `script/style/noscript/svg/iframe/form/nav/header/footer` 与注释 → 块级标签转行、`<td>` 转 ` | ` → 剥标签 → 解实体 → 归一化空白。
2. **噪声行过滤**：`NOISE_PATTERNS` 只匹配**短于 120 字符**的行（镜像站导航、页脚、"Sign in"、"Made with care" 之类），长行一律保留，所以正文里的短句不会被误删。

标题优先取 `<title>` 并剥掉 ` - Freedium` / ` - Medium` 后缀；取不到则用正文前 12 行里第一条 12–160 字符的非噪声行兜底。

### 两个踩过的坑

**① 属性值里的 `>` 会击穿朴素标签匹配。** freedium 用 Tailwind，class 里有 `[&>svg]:px-3` 这类任意变体——属性值中出现 `>`。若用 `<[^>]+>` 剥标签，匹配会在属性中间的 `>` 处截断，整段 class 文本（`svg]:px-3 size-9 text-zinc-600 hover:bg-amber-500/10 ...`）直接漏进正文，且因为拼成的行很长，噪声过滤也拦不住。

解法是「引号感知」的正则：

```python
_ATTR = r"""(?:[^>"']|"[^"]*"|'[^']*')*"""
_TAG  = re.compile(r"<" + _ATTR + r">")
```

JS 版同理，但**正则要带 `u` 标志**，否则 `🎉`（代理对）会被拆成两个码元写进字符类而永远匹配不上——这正是 emoji 噪声行在 JS 版漏网、在 Python 版正常的原因（Python 字符串按码点处理，没有这个问题）。

**② 空 `<pre>` 不该产出空代码围栏。** freedium 页面里有不少 UI 用的空 `<pre>`，直接套围栏会得到一串空的 ``` ``` ```。markdown 化时对 `strip()` 后为空的一律丢弃。

## 已知无害现象

freedium 页面里部分段落（如图示、目录树）**内容会出现两次**——这是镜像页自身把正文渲染了两份（推测为复制/打印用的隐藏副本），不是清洗 bug：text 与 markdown 两种格式重复次数一致，且字符数与线上原实现对得上（RAG vs OKF 那篇 14865 字符）。要消重得靠启发式切正文容器，收益不抵误删风险，故保持原样。

## 已验证行为

- ✅ 正常文章：`freedium-mirror.cfd`，RAG vs OKF 那篇 14865 字符（text）/ 约 1.5 万字符（markdown）
- ✅ 不存在的文章：链上四站依次返回 `article_not_found` / `mirror_parked` / `mirror_render_failed` / `cloudflare_blocked`，最终报"镜像上找不到该文章"，退出码 2
- ✅ 非 Medium 域名：直接拒绝，退出码 3，不发起任何网络请求
- ✅ `--out` 写文件、元信息走 stdout，中文无乱码
- ✅ markdown 模式无 HTML 属性残渣、无空代码围栏、无 emoji 噪声行
- ✅ MCP server（`mcp/`）经 stdio 走 `initialize` → `tools/list` → `tools/call` 抓取成功
