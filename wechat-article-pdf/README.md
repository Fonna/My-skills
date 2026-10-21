# 公众号图片文章转 PDF（wechat-article-pdf）

把「纯图片流」的微信公众号文章（教辅 / 试卷 / 练习册类，正文由 `<img data-src>` 堆叠、几乎无文字层）抓取下来，下载原图，区分**题目**与**答案**，分别拼成两个 A4 打印 PDF，并把原图归档。

## 典型场景

用户发来 `https://mp.weixin.qq.com/s/xxxx` 链接，说「帮我把里面的图片拼成 PDF，题目和答案分开存」。

## 用法

```bash
PY="C:/Users/YQN/.workbuddy/binaries/python/envs/default/Scripts/python.exe"

# 1) 抓原文 + 下载原图（输出目录用绝对路径）
$PY scripts/fetch_images.py --url "<公众号链接>" --outdir "D:/tmp/wx_out"

# 2) 逐张 Read <outdir>/images/img_NN.jpg，区分题目/答案图序号

# 3) 拼两个 PDF（1-based 序号，对应 img_NN.jpg 的 NN）
$PY scripts/make_pdfs.py --outdir "D:/tmp/wx_out" \
    --name "练习名称" \
    --questions 1,2,3,4,5,6,7 \
    --answers 8,9,10,11,12,13,14
```

## 依赖

`pip install pillow reportlab`（装在受管 venv 内）。

## 输出

- `<outdir>/<练习名>-题目.pdf`
- `<outdir>/<练习名>-答案.pdf`
- `<outdir>/原图/`（原图归档）

## 重要提醒

很多公众号发的是「预览 / 试读版」，只放了原文档的部分页（如每隔 3 页发 1 页），文章里**没有**完整版。完整版通常由该号通过菜单 / 自动回复关键词 / 留言区网盘链接单独分发。详见 `SKILL.md` 的「预览版陷阱」与「关键坑」。

## 脚本说明

- `scripts/fetch_images.py`：抓 HTML → 提取 `data-src` 原图 URL（去重保序）→ 下载原图（带 `Referer`）→ 生成 `manifest.json` / `report.txt`，并尝试从 `og:title` 提取文章标题。
- `scripts/make_pdfs.py`：按给定题目/答案序号，用 reportlab 以 A4 contain 适配拼成两个 PDF，并归档原图。
