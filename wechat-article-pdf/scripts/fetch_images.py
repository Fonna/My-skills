#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取微信公众号图片文章并下载原图。

用法:
  python fetch_images.py --url "<公众号文章链接>" --outdir "<绝对输出目录>"

产出:
  <outdir>/images/img_NN.jpg   原图(按文章顺序, 1-based)
  <outdir>/manifest.json       每张图的尺寸/字节数/原图URL
  <outdir>/report.txt          可人读摘要
  (并尝试从 og:title / msg_title 提取文章标题)

关键实现点(踩坑沉淀):
  - 图片是懒加载的, 真地址在 data-src (不是 src)
  - 拿原图要把 /640?wx_fmt=TYPE 换成 /0?wx_fmt=TYPE
  - 下载必须带 Referer: https://mp.weixin.qq.com/ 否则 403
  - 抓 HTML 用桌面 UA
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": DESKTOP_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://mp.weixin.qq.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def extract_body(html: str) -> str:
    i = html.find('id="js_content"')
    if i < 0:
        return html
    j = html.find("rich_media_area_extra", i)
    if j < 0:
        j = len(html)
    return html[i:j]


def extract_title(html: str) -> str:
    m = re.search(r'<meta property="og:title" content="([^"]*)"', html)
    if m:
        return m.group(1).strip()
    m = re.search(r"var msg_title = '([^']*)'", html)
    if m:
        return m.group(1).strip()
    return ""


def extract_images(body: str):
    """提取 data-src 原图 URL, 去重保序。"""
    items = []
    for m in re.finditer(r'data-src="(https://mmbiz\.qpic\.cn/[^"]+)"', body):
        items.append(m.group(1))
    seen, uniq = set(), []
    for u in items:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def to_original(url: str) -> str:
    """缩略图 /640?wx_fmt=xxx -> 原图 /0?wx_fmt=xxx。"""
    return re.sub(r"/640(\?wx_fmt=\w+)", r"/0\1", url)


def download(url: str, path: str) -> int:
    headers = {
        "User-Agent": DESKTOP_UA,
        "Referer": "https://mp.weixin.qq.com/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }
    last_err = None
    for u in (to_original(url), url):
        try:
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            if len(data) > 3000:
                with open(path, "wb") as f:
                    f.write(data)
                return len(data)
            last_err = f"文件过小({len(data)}B), 疑似非图片"
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise last_err if last_err else RuntimeError("下载失败")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="公众号文章链接")
    ap.add_argument("--outdir", required=True, help="输出目录(建议绝对路径)")
    args = ap.parse_args()

    outdir = os.path.abspath(args.outdir)
    imgdir = os.path.join(outdir, "images")
    os.makedirs(imgdir, exist_ok=True)

    print(f"[1/4] 抓取 HTML: {args.url}")
    try:
        html = fetch_html(args.url)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: 抓取 HTML 失败: {e}")
        sys.exit(2)

    title = extract_title(html)
    print(f"     文章标题: {title}")

    body = extract_body(html)
    urls = extract_images(body)
    print(f"[2/4] 提取到 {len(urls)} 张图片(去重后)")
    if not urls:
        print("ERROR: 未找到图片, 可能正文不是图片流或结构已变化")
        sys.exit(2)

    manifest = {"title": title, "images": []}
    for idx, url in enumerate(urls, 1):
        path = os.path.join(imgdir, f"img_{idx:02d}.jpg")
        try:
            size = download(url, path)
            manifest["images"].append(
                {"idx": idx, "file": os.path.relpath(path, outdir),
                 "bytes": size, "orig_url": url}
            )
            print(f"     img_{idx:02d}: {size // 1024} KB")
        except Exception as e:  # noqa: BLE001
            print(f"     img_{idx:02d}: 下载失败 {e}")
            manifest["images"].append({"idx": idx, "file": None, "error": str(e)})
        time.sleep(0.3)

    # 维度(可选, 用 Pillow; 失败不影响主流程)
    try:
        from PIL import Image

        for it in manifest["images"]:
            if it.get("file"):
                with Image.open(os.path.join(outdir, it["file"])) as im:
                    it["width"], it["height"] = im.size
    except Exception:  # noqa: BLE001
        pass

    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    with open(os.path.join(outdir, "report.txt"), "w", encoding="utf-8") as f:
        f.write(f"文章标题: {title}\n图片数: {len(urls)}\n\n")
        for it in manifest["images"]:
            if it.get("width"):
                dims = f'{it["width"]}x{it["height"]}'
            else:
                dims = "?"
            f.write(f'img_{it["idx"]:02d}: {it.get("bytes", 0) // 1024} KB  {dims}\n')

    print(f"[4/4] 完成。原图在 {imgdir}, manifest/report 已写入 {outdir}")
    print("下一步: 逐张查看 images/img_NN.jpg 区分题目/答案, 再运行 make_pdfs.py")


if __name__ == "__main__":
    main()
