#!/usr/bin/env bash
# medium-fetch MCP server 启动包装。
#
# 职责：
#   1. 选 node（优先 /usr/local/bin/node、/usr/bin/node，其次 PATH）。
#   2. 显式注入代理环境变量 —— mcp-client 的 stdio 子进程走 scrubbedParentEnv()，
#      宿主从 /etc/profile.d/proxy.sh 继承的代理变量会被丢弃，故在此重新注入。
#      不覆盖调用方已显式设置的值。
#   3. exec 起 server.cjs（JSON-RPC over stdio，日志只走 stderr）。
#
# 路径按脚本自身位置推导，仓库放哪都能跑。
set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 用 .cjs 后缀：本目录 package.json 声明了 "type": "module"，
# CommonJS 实现需 .cjs 才能被 node 正确加载。
SERVER="$BUNDLE_DIR/server.cjs"

# ── 选 node ──────────────────────────────────────────────────────────────
NODE_BIN="${MEDIUM_FETCH_NODE:-}"
if [[ -z "$NODE_BIN" ]]; then
  for c in /usr/local/bin/node /usr/bin/node /opt/node/bin/node; do
    if [[ -x "$c" ]]; then NODE_BIN="$c"; break; fi
  done
fi
if [[ -z "$NODE_BIN" ]]; then
  NODE_BIN="$(command -v node || true)"
fi
if [[ -z "$NODE_BIN" ]]; then
  echo "medium-fetch-mcp: node not found. Install Node.js first." >&2
  exit 1
fi

# ── 注入代理（与 /etc/profile.d/proxy.sh 保持一致）───────────────────────
# 访问境外站点（medium.com / freedium 镜像）需走 mihomo 代理。
export https_proxy="${https_proxy:-http://127.0.0.1:7890}"
export http_proxy="${http_proxy:-http://127.0.0.1:7890}"
export HTTPS_PROXY="$https_proxy"
export HTTP_PROXY="$http_proxy"
export ALL_PROXY="${ALL_PROXY:-socks5://127.0.0.1:7890}"
export all_proxy="$ALL_PROXY"

exec "$NODE_BIN" "$SERVER"
