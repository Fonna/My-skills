# Chrome 阅读清单导出

从本机已安装的 `chrome-reading-list` skill 归档，保留原始 `SKILL.md` 和 `scripts/export_reading_list.py`。技能触发规则与解析细节见 [SKILL.md](SKILL.md)。

## 功能

- 读取 Chrome Profile 的 `Sync Data/LevelDB`，导出 Reading List / 稍后阅读。
- 输出 Markdown 清单，可同时输出包含全部字段的 JSON。
- 显示总条数、已读 / 未读数量、添加时间范围和最近 10 条。
- 支持指定 Profile 和 Chrome User Data 目录；只读浏览器数据，Chrome 运行时也可使用。

## 运行环境

需要 Python 3。脚本首次读取数据时会按需通过 `pip` 安装 `cramjam`，用于 Snappy 解压；首次安装需要网络，也可提前安装：

```bash
python -m pip install cramjam
```

## 使用方法

在仓库根目录执行；以下示例把个人导出结果写到仓库外：

```powershell
python chrome-reading-list/scripts/export_reading_list.py --out "$env:USERPROFILE/Documents/chrome_reading_list.md" --json "$env:USERPROFILE/Documents/chrome_reading_list.json"
```

默认读取 Windows 下 `%LOCALAPPDATA%/Google/Chrome/User Data` 的 `Default` Profile。其他 Profile 或不同位置的 Chrome 数据可显式指定：

```bash
python chrome-reading-list/scripts/export_reading_list.py --profile "Profile 1" --user-data "<Chrome User Data 目录>" --out "<仓库外的输出目录>/chrome_reading_list.md"
```

查看完整命令行参数（不会读取 Chrome 数据或安装依赖）：

```bash
python chrome-reading-list/scripts/export_reading_list.py --help
```

安装到支持文件夹形式技能的平台时，整体复制 `chrome-reading-list/` 到对应技能目录，保留 `scripts/`。仓库用于管理技能本身，个人阅读清单导出结果请保存在仓库外。
