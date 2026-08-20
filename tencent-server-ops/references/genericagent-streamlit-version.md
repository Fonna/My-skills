# GenericAgent streamlit 版本问题

## 症状
GenericAgent 的 Streamlit 界面报错：
```
streamlit.errors.StreamlitAPIException: A fragment tried to write to a container created outside the fragment, but that container was not written to during the initial run
```
或前端弹窗：
```
Bad message format / Bad 'setIn' index 2 (should be between [0, 0])
```

## 根因
GA 的 `render_main_stream` fragment 会把 `st.expander` 写进 `mount_main_stream()` 创建的外部容器 `frozen_host`。

- **streamlit 1.61.0**（最新）：加了严格的 `_get_or_create_outside_wrapper` 检查，触发 fragment 异常。
- **streamlit 1.39.0**：没有 fragment 异常，但 DeltaGenerator 索引处理太旧，触发前端 `setIn` 弹窗。
- **streamlit 1.55.0**：两者都没有。**这是工作版本。**

真正的修复是**版本降级**，不是改代码。曾尝试过 `with frozen_host: pass` 的 fragment 修复，证明无效并已回退。

## 验证某个版本有没有严格检查
```bash
ssh tencent 'grep -c "A fragment tried to write to a container created outside" /root/GenericAgent/.venv/lib/python3.12/site-packages/streamlit/delta_generator.py'
# 0 = 宽松（可用），1 = 严格（会报错）
```

## 修复
```bash
ssh tencent '/root/.local/bin/uv pip install "streamlit==1.55.0" --python /root/GenericAgent/.venv/bin/python'
ssh tencent 'systemctl restart genericagent'
```

## 防复发
`pyproject.toml` 第 23 行依赖还写的是 `streamlit>=1.28`（未锁上限）。如果重跑 `uv pip install -e ".[ui]"` 会拉到 1.61+ 重新触发问题。应改为 `streamlit>=1.28,<1.56` 锁住上限。

> 截至上次记录，这个 pyproject 锁版本改动**尚未完成**，是 pending 项。

## 中文化补丁管理
stapp.py 有 10 处 UI 中文化改动（Cowork->协作 等），通过 git stash + 本地 patch 管理：
- 本地 patch：`D:\GenericAgent\ga-i18n-zh.patch`（基于 commit 284b332）
- 服务器备份：`/root/GenericAgent/frontends/stapp.py.bak`
- 更新流程：`git stash push -m 'i18n-zh' frontends/stapp.py` -> `git pull` -> `git stash pop` -> `systemctl restart genericagent`

mykey.py 用火山引擎 GLM-5.2，本地源文件 `D:\GenericAgent\mykey.py`。
