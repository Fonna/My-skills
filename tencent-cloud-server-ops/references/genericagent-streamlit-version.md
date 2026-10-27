> 来源：原 tencent-server-ops 的历史排障记录。合并时未登录服务器核实现状；日期、版本和配置均须按本次任务复核。文中修复步骤不构成自动升级、改配置或重启授权。

# GenericAgent streamlit 版本问题

> **2026-08-28 更新：本问题已被上游修复，当前工作版本是 streamlit 1.62.0，不再是 1.55.0。**
> 下文的历史结论仅用于理解旧日志，不要再按它降级。

## 现状（2026-08-28）

- 上游 GA 在 commit `30b24ad` / `b0d2703` / `d6403d9` 中把 fragment 写外部容器的问题修掉了
  （"own stream bubble inside fragment"、"repaint stream host fully each tick for Streamlit 1.62 wrapper reset"），并把 `pyproject.toml` 改为 `streamlit>=1.62`。
- 服务器已升级 GA 到 `17d9f4d` + streamlit 1.62.0，`genericagent` 服务正常，日志无 StreamlitAPIException。
- **不要**再按旧结论把 streamlit 锁回 1.55：新代码按 1.62 的行为写的，锁旧版反而可能不兼容。

## 升级自动化（重要）

服务器上有两层自动化，升级 GA 时要知道它们的存在：

1. **git post-merge hook**（`/root/GenericAgent/.git/hooks/post-merge`）：`git pull` 之后自动
   重装依赖（含 streamlit 升级）、重启 genericagent、用 `.ga-local-zh.patch` 恢复 stapp.py 中文化。
   所以 `git pull` 一条命令就会触发完整升级链路。
2. **`/root/GenericAgent/upgrade.sh`**：手动升级脚本（stash → pull → 恢复中文化 → 重启）。
   ⚠️ 脚本里"锁定 streamlit <1.61"的步骤已过时（上游要 >=1.62），跑之前先检查/删掉该步骤。

## 历史根因（供理解旧日志）

GA 的 `render_main_stream` fragment 会把 `st.expander` 写进 `mount_main_stream()` 创建的外部容器 `frozen_host`。

- **streamlit 1.61.0**：加了严格的 `_get_or_create_outside_wrapper` 检查，触发 fragment 异常。
- **streamlit 1.39.0**：DeltaGenerator 索引处理太旧，触发前端 `setIn` 弹窗。
- **streamlit 1.55.0**：两者都没有，因此曾是工作版本。
- **streamlit 1.62.x**：上游 GA 代码已适配，为当前工作版本。

## 中文化补丁管理

stapp.py 有约 10 处 UI 中文化改动（Cowork->协作 等），现通过服务器本地 patch 管理：

- 服务器 patch：`/root/GenericAgent/.ga-local-zh.patch`（post-merge hook 用 `git apply --3way` 恢复）
- 服务器备份：`/root/GenericAgent/frontends/stapp.py.bak`；另有手工快照 `/root/stapp-zh-backup-20260828.py`
- 若 patch 因上游大改 apply 失败：从备份文件里取中文文案，对照新版 stapp.py 手工重新应用
- pyproject.toml 曾本地锁 `<1.61`，2026-08-28 起跟随上游（该锁定不再恢复）
- 本地定制（.gitignore 忽略项、memory 笔记）改动放在 git stash 里备查：`git stash list`

mykey.py 用火山引擎 GLM-5.2，本地源文件 `D:\GenericAgent\mykey.py`。
