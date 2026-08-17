---
name: "中译英默写本PDF生成"
description: "用户提供单词书/词汇表截图或照片、要求生成中译英默写本或听写纸并打印用 PDF 时使用。产出一行两列卡片式、保留音标、去掉词性、中文自动换行、带页码的 A4 PDF。触发词：默写本、听写、中译英、单词表、词汇书、dictation。"
---

# 中译英默写本 PDF 生成

当用户发来单词书/词汇表页面图片（实拍或截图），要求做「中译英默写本 / 听写纸 / 默写纸」并要能直接打印的 PDF 时，按本规格执行。

## 输出规格（固定，不要随意改动）

- **版式**：一行两列卡片式（CSS `grid-template-columns: 1fr 1fr`），每条是一个带浅边框的小卡片。
- **每条包含**：序号（如 W-ID）+ 音标 IPA（保留）+ 中文释义（保留，过长自动换行 `word-break: break-word`）+ 2 行书写横线（供学生默写英文）。
- **去掉词性**（n. / v. / adj. 等不显示，把空格留给学生）。
- **音标保留**（作为读音提示）。
- **顶部**：标题 + 班级 / 姓名 / 日期填写栏（用 `<input>` 占位）。
- **分组**：按「原书页」做逻辑 section header（如「第 1 页　W-ID 1622 ~ 1631」），物理 A4 页由内容流式排版决定，不必 1:1 对应。
- **页码**：每页底部正中盖「第 N 页 / 共 M 页」。
- **纸张**：A4，`@page { size: A4; margin: 1.4cm; }`，单面印刷。

## 工作流程

1. **识别单词**：按图片现有顺序逐条提取 `序号 + 音标 + 中文释义`，忽略例句、词形拓展、派生词（除非用户要求）。图片裁切导致某条释义不全时，用常见释义并在回复中明确提示用户确认。
2. **续接已有文件**：若本次是「再加几页」，读取已有 HTML/PDF，按 W-ID 连续追加，并更新文件名里的范围。
3. **生成 HTML**（模板见下）。
4. **HTML → PDF**：用本机 Chrome 无头模式打印（命令见下）。
5. **加页码**：用 PyMuPDF 在每页底部正中插入「第 N 页 / 共 M 页」。
6. **合并为单一文件**：文件名与 W-ID 范围一致（如 `中译英默写本_W1622-1658.pdf`），删除中间产物。

## HTML 模板（关键结构）

```html
<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>中译英 默写本</title>
<style>
  @page { size: A4; margin: 1.4cm; }
  * { box-sizing: border-box; }
  body { font-family: "Microsoft YaHei","PingFang SC","Noto Sans CJK SC",Arial,sans-serif;
         max-width: 820px; margin: 0 auto; padding: 22px 26px; color: #1a1a1a; font-size: 14px; }
  h1 { text-align:center; font-size:23px; margin:0 0 6px; }
  .meta { text-align:center; color:#666; font-size:12px; margin-bottom:20px;
          padding-bottom:12px; border-bottom:1.5px solid #333; }
  .meta input { border:none; border-bottom:1px solid #999; width:86px; text-align:center;
                font-family:inherit; font-size:12px; color:#333; background:transparent; }
  .page-section { margin-bottom:22px; }
  .page-header { font-size:14px; font-weight:700; padding:5px 10px; background:#f1f1f1;
                 border-left:4px solid #444; margin-bottom:12px; }
  .dict-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px 16px; }
  .entry { border:1px solid #e3e3e3; border-radius:4px; padding:7px 9px;
           break-inside:avoid; page-break-inside:avoid; }
  .entry-top { margin-bottom:2px; }
  .entry-no { font-weight:700; color:#555; margin-right:7px; font-size:13px; }
  .entry-ipa { color:#999; font-style:italic; font-size:12px;
               font-family:"Cambria","Times New Roman",serif; }
  .entry-cn { display:block; line-height:1.5; margin:1px 0 5px; word-break:break-word; }
  .lines { margin-top:2px; }
  .line { border-bottom:1.3px solid #555; height:27px; }
  @media print { body{padding:0; max-width:none;} .entry{break-inside:avoid;} input{color:#000;} }
</style></head><body>
<h1>中译英 默写本</h1>
<div class="meta">W-ID 1622 ~ 1658　·　共 37 词　　班级：<input>　　姓名：<input>　　日期：<input></div>
<!-- 每个 section：<div class="page-section"><div class="page-header">第 N 页　W-ID x~y（共 k 词）</div><div class="dict-grid"> ...entries... </div></div> -->
<div class="page-section">
  <div class="page-header">第 1 页　W-ID 1622 ~ 1631（共 10 词）</div>
  <div class="dict-grid">
    <div class="entry">
      <div class="entry-top"><span class="entry-no">1622</span><span class="entry-ipa">/tʌtʃ/</span></div>
      <span class="entry-cn">触摸；接触；联系</span>
      <div class="lines"><div class="line"></div><div class="line"></div></div>
    </div>
    <!-- 更多 .entry ... -->
  </div>
</div>
</body></html>
```

## Chrome 转 PDF（本机无头打印）

```bash
CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
SRC_HTML=".../dict.html"      # 含中文时先复制到无中文名临时路径
OUT_PDF=".../output.pdf"
UDD="C:/Users/YQN/AppData/Local/Temp/chrome_udd"
rm -rf "$UDD"
"$CHROME" --headless=new --disable-gpu --no-sandbox --user-data-dir="$UDD" \
          --no-pdf-header-footer --print-to-pdf="$OUT_PDF" "file:///$SRC_HTML"
```

要点：
- 必须带 `--user-data-dir`，否则报 `Missing headless user data directory`。
- HTML 路径含中文时 Chrome 的 `file:///` 易出错，先 `cp` 到 ASCII 临时路径再转。
- Edge 亦可：`/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`。

## PyMuPDF 加页码

```python
import fitz, os
src = r"...\中译英默写本_W1622-1658.pdf"
out = r"...\中译英默写本_W1622-1658.pdf"   # 注意：被预览锁定时 os.replace 会 PermissionError
doc = fitz.open(src)
total = doc.page_count
for i, page in enumerate(doc):
    text = f"第 {i+1} 页 / 共 {total} 页"
    tw = fitz.get_text_length(text, fontname="china-s", fontsize=9)
    x = (page.rect.width - tw) / 2
    y = page.rect.height - 26
    page.insert_text((x, y), text, fontname="china-s", fontsize=9, color=(0,0,0))
doc.save(out); doc.close()
```

要点：
- `fitz` 已弃用但可用；导入 `pymupdf` 亦可。
- 内置 CJK 字体 `china-s`（简体）无需外部字体文件即可渲染中文。
- **覆盖被预览面板锁定的 PDF 会失败**：始终先保存为带后缀的新文件（如 `_带页码.pdf`），处理完再 `rm -f` 旧文件、`mv` 新文件为统一名。

## 环境要点

- 受管 Python venv：`C:/Users/YQN/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（PyMuPDF：`python -m pip install pymupdf`）。
- 删除被预览占用的旧 PDF：直接 `rm -f` 通常可行（Windows 删除待处理）；若失败再请用户关闭预览。
- 最终只保留一个 PDF，文件名随 W-ID 范围更新。
