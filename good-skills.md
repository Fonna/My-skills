# 优秀 Skill 收藏

记录值得收藏的外部（非自制）Skill / Skill 合集：来源、基础介绍、安装方式、适用平台与使用备注。新增条目时在索引表加一行，并按下文模板补充详情。

---

## 索引

| 名称 | 来源 | 类型 | 适用平台 | 一句话简介 |
| --- | --- | --- | --- | --- |
| duckdb-skills | [duckdb/duckdb-skills](https://github.com/duckdb/duckdb-skills) | Claude Code 插件（含 6 个 skill） | macOS / Linux（Windows 暂不完整支持） | DuckDB 官方出品，把本地/远程数据文件直接变成可 SQL 探索的数据库 |

---

## duckdb-skills

- **地址**：<https://github.com/duckdb/duckdb-skills>
- **作者/维护方**：DuckDB 官方（duckdb org）
- **协议**：MIT　|　**热度**：约 600 stars（2026-10 记录）
- **形态**：Claude Code 插件（plugin），内含 6 个 skill，通过 `/duckdb-skills:<skill-name>` 调用

### 基础介绍

DuckDB 官方发布的 Claude Code 插件，为 Agent 提供「用 DuckDB 探索数据」的全套技能：挂载数据库、跑 SQL、读任意格式数据文件、查官方文档全文检索，甚至翻过往会话日志找回上下文。所有 skill 共享同一份 `state.sql` 会话状态（ATTACH/USE/LOAD、secrets、宏），跨 skill 复用、追加式幂等。

### 包含的 Skills

| Skill | 用途 |
| --- | --- |
| `attach-db` | 挂载 DuckDB 数据库文件，自动探查 schema（表/列/行数）并写会话状态，支持多库叠加挂载 |
| `query` | 对已挂载数据库或临时文件执行 SQL，支持自然语言提问，使用 DuckDB Friendly SQL 方言 |
| `read-file` | 读任意数据文件——CSV / JSON / Parquet / Avro / Excel / spatial / SQLite / Jupyter 等，本地或 S3/GCS/Azure/HTTPS 远程，按扩展名自动识别格式 |
| `duckdb-docs` | 全文检索 DuckDB 与 DuckLake 官方文档、博客（托管索引，HTTPS 直查，可选本地缓存）；SQL 报错时会自动用它排障 |
| `read-memories` | 检索过往 Claude Code 会话日志，找回决策、模式和未完成事项；大结果集自动卸载到临时 DuckDB 文件下钻 |
| `install-duckdb` | 安装/更新 DuckDB 扩展，支持社区扩展 `name@repo` 语法，`--update` 可顺带检查 CLI 版本 |

### 安装方式

Claude Code 内执行（GitHub marketplace 方式，官方市场上架中）：

```
/plugin marketplace add duckdb/duckdb-skills
/plugin install duckdb-skills@duckdb-skills
```

更新：

```
/plugin marketplace update duckdb-skills
/plugin update duckdb-skills@duckdb-skills
```

本地开发/调试：clone 仓库后 `claude --plugin-dir .` 加载。前置条件：需安装 DuckDB CLI（未装时 skill 会引导用 `install-duckdb` 安装）。

### 适用平台与注意事项

- 官方仅在 **macOS / Linux** 测试过；**Windows 尚未完整支持**，部分 shell 命令与路径处理可能异常（对 Windows 为主力机的使用者，建议 WSL 内使用，或等官方兼容性改进）。
- 会话状态文件位置可选：项目内 `.duckdb-skills/state.sql`（可 gitignore）或家目录 `~/.duckdb-skills/<project>/state.sql`。

### 备注

（待补：实际使用感受、与自有工作流的结合点等）
