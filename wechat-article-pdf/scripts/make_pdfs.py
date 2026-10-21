#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把公众号文章原图拼成两个 A4 打印 PDF(题目 / 答案) 并归档原图。

用法:
  python make_pdfs.py --outdir <目录> --name "<练习名称>" \
      --questions 1,2,3,4,5,6,7 --answers 8,9,10,11,12,13,14

说明:
  - 原图默认在 <outdir>/images/img_NN.jpg (由 fetch_images.py 产出)
  - 序号为 1-based, 对应 img_NN.jpg 的 NN
  - A4 竖版, contain 等比适配居中留白, 绝不裁切内容
  - 生成 <outdir>/<名称>-题目.pdf 与 <outdir>/<名称>-答案.pdf
  - 原图归档到 <outdir>/原图/
"""
import argparse
import os
import shutil
import sys

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build(indices, imgdir: str, out_pdf: str):
    PW, PH = A4  # 595.27 x 841.89 pt
    c = canvas.Canvas(out_pdf, pagesize=A4)
    drawn = 0
    for n in indices:
        p = os.path.join(imgdir, f"img_{n:02d}.jpg")
        if not os.path.exists(p):
            print(f"  跳过 img_{n:02d}（文件不存在）")
            continue
        im = Image.open(p)
        iw, ih = im.size
        scale = min(PW / iw, PH / ih)  # contain
        w, h = iw * scale, ih * scale
        x, y = (PW - w) / 2, (PH - h) / 2
        c.drawImage(p, x, y, w, h)
        c.showPage()
        drawn += 1
    c.save()
    print(f"  生成 {out_pdf}（{drawn} 页）")


def parse_list(s: str):
    return [int(x) for x in s.split(",") if x.strip()] if s else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--questions", default="", help="题目图序号, 逗号分隔")
    ap.add_argument("--answers", default="", help="答案图序号, 逗号分隔")
    args = ap.parse_args()

    outdir = os.path.abspath(args.outdir)
    imgdir = os.path.join(outdir, "images")
    if not os.path.isdir(imgdir):
        print("ERROR: 找不到 images/ 目录, 请先运行 fetch_images.py")
        sys.exit(2)

    q = parse_list(args.questions)
    a = parse_list(args.answers)
    if not q and not a:
        print("ERROR: 至少需要 --questions 或 --answers 之一")
        sys.exit(2)

    base = args.name.strip()
    print(f"[1/2] 练习名称: {base}")
    if q:
        build(q, imgdir, os.path.join(outdir, f"{base}-题目.pdf"))
    if a:
        build(a, imgdir, os.path.join(outdir, f"{base}-答案.pdf"))

    arch = os.path.join(outdir, "原图")
    os.makedirs(arch, exist_ok=True)
    n = 0
    for f in os.listdir(imgdir):
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            shutil.copy2(os.path.join(imgdir, f), os.path.join(arch, f))
            n += 1
    print(f"[2/2] 原图已归档到 {arch}（{n} 张）")
    print("提示: 文件名中的练习名称若需调整, 直接重命名 PDF 即可。")


if __name__ == "__main__":
    main()
