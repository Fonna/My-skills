---
name: chrome-reading-list
description: 读取并导出本机 Chrome 的阅读清单（Reading List / 稍后阅读）。当用户提到 阅读清单、reading list、稍后阅读、导出浏览器里保存的文章或网页列表、查看未读条目、整理 Chrome 收藏的文章时使用——即使没有明确说"导出"，凡涉及 Chrome 阅读清单内容的查看、整理、统计、转换都应触发。内置纯 Python LevelDB 解析器，Chrome 运行中即可一条命令导出 Markdown/JSON。
---

# Chrome 阅读清单导出

## 背景：数据在哪

Chrome 阅读清单**不在**书签文件（`Bookmarks` JSON）里，通常也不存在 `User Data\<Profile>\ReadingList` 目录——先别去这两个地方找。

数据实际存放在 **`User Data\<Profile>\Sync Data\LevelDB`**（同步存储），键名：

- `reading_list-dt-<url>` — 条目本体（protobuf）：f1=规范 URL，f2=标题，f3=显示 URL，f4=添加时间（**Unix 微秒**），f5=更新时间，f6=已读标记（0/1）
- `reading_list-md-<url>` — 同步元数据（client_tag_hash 等，导出条目用不到）

URL 和标题是明文，无需解密。数据可能包含多设备同步合并的旧条目。

## 操作

运行内置脚本（纯只读，Chrome 正在运行也没关系）：

```bash
python "<本 skill 目录>/scripts/export_reading_list.py" --out chrome_reading_list.md
# 可选参数：
#   --json out.json        同时输出 JSON（全字段）
#   --profile "Profile 1"  非 Default 配置时指定
```

脚本会自动 `pip install cramjam`（Snappy 解压依赖），打印摘要（总数/未读数/时间范围/最近 10 条），并把完整清单写成 Markdown 表格（列：序号、已读未读、添加时间、标题、URL）。

然后向用户汇报：总条数、未读/已读数、时间范围、最近添加的几条，并给出导出文件链接。如果用户想按主题归类或转成书签导入 HTML，属于后续加工，基于导出的 Markdown/JSON 做。

## 故障排查

- **结果 0 条**：先用二进制 grep 确认数据确实存在：
  `grep -a -c "reading_list-dt-" "…/Sync Data/LevelDB"/*.ldb`。
  注意 Git Bash 里**没有** `strings` 命令，别用它搜索二进制文件（会静默输出空结果），用 `grep -a` 或 Python。
- **找不到 Profile**：脚本会列出所有含 Sync Data 的 Profile；也可让用户看 `chrome://version` 的 Profile Path。
- **中文乱码**：大量中文走 stdout 管道可能乱码——所以脚本把结果写入 UTF-8 文件，stdout 只打少量摘要。汇报时引用文件内容，不要靠管道输出长文本。

## 已踩过的坑（解析器已内置处理，改代码时注意）

1. LevelDB BlockHandle 的 size **不含**块尾 5 字节（crc+type），读块要切 `raw[off : off+size+5]`。
2. `.ldb` 数据块是 **raw Snappy**（非 framed），必须 `cramjam.snappy.decompress_raw`，用 framed 版会报 "expected stream header"。
3. 块内布局是 `[条目][restart 数组][num_restarts(4)][crc(4)][type(1)]`，条目遍历必须在 restart 数组前停。
4. 时间戳是 **Unix 微秒**（不是 Chrome 1601 epoch），直接 `fromtimestamp(us/1e6)`。
5. protobuf 解析遇到重复字段号时也必须推进 pos 再跳过，否则后续字段整体错位（表现为时间戳全 0）。
