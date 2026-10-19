# medium-fetch MCP server（可选）

把 Medium 文章抓取挂成常驻 MCP 工具。**只想抓一两篇文章的话不需要这个**——直接用 `../scripts/fetch_medium_article.py` 即可。

## 工具

挂载后模型侧可见：

- `mcp__medium-fetch__fetch_medium_article` — 正文纯文本（`format` 可选 `text`/`markdown`/`html`）
- `mcp__medium-fetch__fetch_medium_article_html` — 清洗后的 HTML

返回 `structuredContent`：`url` / `title` / `mirror_used` / `char_count` / `truncated` / `body` / `attempts`。

## 文件

```
mcp/
├── server.cjs              # MCP server 实现（零 npm 依赖，Node 内置模块）
├── run-medium-fetch-mcp.sh # 启动包装（选 node + 注入代理 + exec）
├── package.json            # bundle manifest（name: @local/medium-fetch-mcp）
└── cordis.patch.yml        # DSH @deepseek-ai/dsh-mcp-client 接入配置
```

`server.cjs` 与 Python 脚本共用同一套镜像回退链与失败原因码（`references/mirrors.md`），行为一致。

## DSH 接入

`package.json` 里的 bundle 名是 `@local/medium-fetch-mcp`，需与 harness 的 bundle 目录同名；`cordis.patch.yml` 用绝对路径指向启动脚本，按实际安装位置改：

```yaml
- insert:
    - id: medium-fetch-mcp
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: medium-fetch
        transport: stdio
        command: /path/to/mcp/run-medium-fetch-mcp.sh
        failOnStartupError: true
```

挂载步骤：`dsh` 的 bundle 机制（本地 bundle 放到工作区 → `@local/<name>` link 进对应 profile → 注册进 `profiles/<profile>/dsh.profile.bundles`）。改完 server 无需手动重启，mcp-client 的重连机制会自动重启子进程。

## 为什么零依赖

`server.cjs` 只用 Node 内置模块（`node:child_process`、`node:buffer`、`node:fs`），不依赖 `@modelcontextprotocol/sdk`，也不跑 `npm install`——多数 harness 的 node_modules 里只有 MCP **client** SDK 没有 server SDK。裸 stdio JSON-RPC 只实现客户端必需的最小子集：

`initialize` / `notifications/initialized` / `tools/list` / `tools/call` / `ping` / `resources/list` / `prompts/list`

未知工具 → `-32602`，未知方法 → `-32601`。

## 环境变量

- `MEDIUM_FETCH_NODE` — 指定 node 路径
- `MEDIUM_FETCH_CURL` — 指定 curl 路径

## 与线上实例的关系

本目录源自 DSH 服务器上实际运行的那份（`/srv/deepseek-harness/workspace/medium-fetch-mcp/`），并在此基础上修了两个清洗 bug：**引号感知的标签匹配**（freedium 的 Tailwind class 含 `[&>svg]:` 这类带 `>` 的属性值，朴素 `<[^>]+>` 会把整段 class 漏进正文）与**噪声行的 `u` 标志**（emoji 在 JS 正则字符类里需 `u` 标志才匹配得到）。修法见 `../references/mirrors.md`。

线上那份仍是旧版本，两者行为差异仅限 markdown 输出的清洗质量，镜像链、失败原因码、退出码一致。**改动镜像链时两边都要同步**（以本目录为准回填线上），或反向亦可。
