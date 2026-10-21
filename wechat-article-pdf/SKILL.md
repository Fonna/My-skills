---
name: "公众号图片文章转PDF"
description: "当用户发来微信公众号文章链接(mp.weixin.qq.com/s/...)，且其正文是图片型题目/练习/资料，要求把图片拼接成可打印PDF、或把题目与答案分别存为两个文档时使用。自动抓取原文图片、下载原图、区分题目/答案、按A4拼成打印PDF并归档原图。触发词：公众号、拼接PDF、图片题目、题目PDF、练习PDF、打印、公众号文章图片、mp.weixin.qq.com、把图片拼成pdf。"
---

# 公众号图片文章转 PDF

把一篇「纯图片流」的微信公众号文章（典型场景：教辅/试卷/练习册的图片型题目，一般含题目图与答案图）抓取下来，下载原图，区分题目与答案，**分别拼成两个 A4 打印 PDF**，并把原图归档。

## 适用场景

- 用户发来 `https://mp.weixin.qq.com/s/xxxx` 链接，说「帮我把里面的图片拼成 PDF / 题目和答案分开存」。
- 文章正文由 `<section><img data-src=...></section>` 堆叠而成，几乎无文字层。
- 产出：`<练习名>-题目.pdf` + `<练习名>-答案.pdf` + `原图/`（14 张或 N 张原图）。

## 前置依赖

- Python（受管 venv 优先）：`C:/Users/YQN/.workbuddy/binaries/python/envs/default/Scripts/python.exe`
- 依赖：`pip install pillow reportlab`（在 venv 内装一次即可）
- 脚本路径（skill 装在 `~/.workbuddy/skills/wechat-article-pdf/` 或仓库内均可）：`scripts/fetch_images.py`、`scripts/make_pdfs.py`

## 工作流程（四步）

### 第 1 步：抓取并下载原图

```bash
PY="C:/Users/YQN/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
$PY scripts/fetch_images.py --url "<用户给的公众号链接>" --outdir "<绝对路径输出目录>"
```

- 自动：抓 HTML（桌面 UA）→ 定位 `js_content` 到 `rich_media_area_extra` 之间的正文 → 提取所有 `data-src` 图片（去重保序）→ 把每个 URL 的 `/640?wx_fmt=TYPE` 换成 `/0?wx_fmt=TYPE` 拿**原图** → 带 `Referer: https://mp.weixin.qq.com/` 下载到 `<outdir>/images/img_NN.jpg`。
- 产出：`<outdir>/images/`（原图）、`manifest.json`（每张图的尺寸/字节数）、`report.txt`（可人读摘要）、并尝试从 `og:title`/`msg_title` 取文章标题作练习名候选。

### 第 2 步：区分题目 / 答案（关键，需多模态判断）

逐张用 Read 工具查看 `<outdir>/images/img_NN.jpg`，判断每张是**题目**还是**答案/解析**。判断依据：

1. **页脚页码**：许多教辅每图跨多页，页脚写「第 N 页 / 共 M 页」，据此推断文章是否只发了原文档的部分页（见下方「预览版陷阱」）。
2. **题号连续性**：题目图顶部常有序号 Q1、Q10…，答案图带「答案 / 解析 / 分析 / 解答」字样。
3. **文件体积启发**：答案含解析的图通常比纯题目图更大（可作辅助信号，不作为唯一依据）。
4. **顺序规律**：常见「先全部题目、再全部答案」，但也可能交错，务必逐张确认，不要假设。

把题目图的序号（1-based，对应 `img_NN.jpg` 的 NN）记成列表 Q，答案图记成列表 A。

### 第 3 步：拼接两个 PDF

```bash
$PY scripts/make_pdfs.py --outdir "<同一输出目录>" \
    --name "<练习名称>" \
    --questions 1,2,3,4,5,6,7 \
    --answers 8,9,10,11,12,13,14
```

- A4 竖版，**contain 适配**（等比缩放、居中留白、绝不裁切任何内容），原图约 200 DPI，直接可打印。
- 练习名称取法优先级：**用户明确给定** > 文章封面/标题里的练习名 > 从公众号文章标题提取（去掉「附解析」等后缀）。
- 自动把原图复制到 `<outdir>/原图/` 归档。

### 第 4 步：交付与提醒

- `present_files` 交付两个 PDF。
- **务必提醒用户**：很多公众号发的是「预览/试读版」，只放了原文档的部分页（如每隔 3 页发 1 页），文章里并**没有**完整版。完整版通常由该号通过菜单/自动回复关键词/留言区网盘链接单独分发。若用户要完整版，引导其去公众号内获取链接后再发来，重跑本流程。

## 关键坑（务必遵守，都是踩过的）

1. **`/tmp` 在 Windows 上会变 `C:\tmp`**：Python 里 `open('/tmp/x')` 会落到 `C:\tmp` 而非 Git Bash 的临时目录，易读到旧缓存。脚本一律用 `--outdir` 传**绝对路径**，或在脚本内用 `os.environ['TEMP']`，不要硬编码 `/tmp`。
2. **图片是懒加载的**：正文 `<img>` 真正地址在 `data-src`（不是 `src`）。直接抓 `src` 会拿到占位缩略图或空。
3. **拿原图要改 URL**：`.../640?wx_fmt=jpg` → `.../0?wx_fmt=jpg`（`/0` 是原图，`/640` 是 640 宽缩略图）。下载不带这个替换会得到模糊小图。
4. **下载必须带 Referer**：`Referer: https://mp.weixin.qq.com/`，否则微信 CDN 返回 403。
5. **桌面 UA**：抓 HTML 用桌面浏览器 UA，移动 UA 有时拿不到完整正文。
6. **A4 适配用 contain 不要裁切**：题目/答案图边缘常有关键内容（题号、页码、答案行），`drawImage` 用等比 contain 居中，避免 `crop` 丢内容。
7. **原图比例几乎都是 1709×2393（≈ A4）**，一份图 = 一页 PDF 即可，无需再缩放分页。

## 输出约定

- 文件名：`<练习名>-题目.pdf`、`<练习名>-答案.pdf`。练习名从封面/标题提取，无独立练习名时回退到文章标题。
- 只归档**可复用技能文件**；本 skill 不入库任何个人导出结果。
- 若文章正文其实有文本层（极少数），优先用文本，但本流程面向「纯图片流」场景。

## 环境要点

- 受管 Python venv：`C:/Users/YQN/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（装 `pillow` + `reportlab`）。
- 同号其他文章链接/外链可从 HTML 里提取辅助判断；但「阅读原文」外链、网盘链接通常在正文之外，需用户在微信端查看。
