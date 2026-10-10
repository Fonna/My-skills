#!/usr/bin/env python3
# Agnes AI image generation (agnes-image-2.5-flash / 2.1-flash) — Linux port of generate_image.ps1
#
# Usage:
#   python3 generate_image.py params.json
#   python3 generate_image.py --prompt "..." [--size 2K] [--ratio 16:9] [--image URL ...] \
#       [--model agnes-image-2.5-flash] [--out-dir outputs/agnes-image] [--b64]
#
# Params JSON (UTF-8): prompt(required), model, size, ratio, image[](urls/data-uris),
#   return_base64(bool), out_dir, extras(object merged into request body)
# Prints "SAVED=<path>" per generated image. Exit 1 on failure with API error JSON.
# Key source (never echoed): env AGNES_API_KEY, else ~/.config/dsh-secrets/agnes-api-key

import argparse
import base64
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

API = "https://apihub.agnes-ai.com/v1/images/generations"
TIMEOUT = 300


def fail(msg):
    print(msg)
    sys.exit(1)


def load_key():
    key = os.environ.get("AGNES_API_KEY", "").strip()
    if key:
        return key
    p = pathlib.Path.home() / ".config" / "dsh-secrets" / "agnes-api-key"
    try:
        if p.is_file():
            key = p.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    if key:
        return key
    fail(
        "MISSING_KEY: AGNES_API_KEY 未设置，且 ~/.config/dsh-secrets/agnes-api-key 不存在或为空。"
        "在服务器上执行: echo -n 'Key' > ~/.config/dsh-secrets/agnes-api-key && chmod 600 ~/.config/dsh-secrets/agnes-api-key"
        "（Key 从 platform.agnes-ai.com 控制台获取；不要把 Key 粘贴到对话里）"
    )


def main():
    ap = argparse.ArgumentParser(description="Agnes AI image generation")
    ap.add_argument("json", nargs="?", help="params JSON file (UTF-8)")
    ap.add_argument("--prompt")
    ap.add_argument("--model")
    ap.add_argument("--size")
    ap.add_argument("--ratio")
    ap.add_argument("--image", action="append", default=[],
                    help="reference image URL / data URI (repeatable)")
    ap.add_argument("--out-dir", dest="out_dir")
    ap.add_argument("--b64", action="store_true", help="request/return base64")
    args = ap.parse_args()

    p = {}
    if args.json:
        jf = pathlib.Path(args.json)
        if not jf.is_file():
            fail(f"PARAMS_NOT_FOUND: {args.json}")
        try:
            p = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            fail(f"BAD_JSON: {e}")
        if not isinstance(p, dict):
            fail("BAD_JSON: top-level must be an object")

    prompt = args.prompt or p.get("prompt")
    if not prompt:
        fail("MISSING_PROMPT")

    model = args.model or p.get("model") or "agnes-image-2.5-flash"
    size = args.size or p.get("size") or "2K"
    ratio = args.ratio if args.ratio is not None else p.get("ratio")
    images = list(args.image) if args.image else list(p.get("image") or [])
    return_base64 = bool(args.b64 or p.get("return_base64"))
    out_dir = args.out_dir or p.get("out_dir") or "outputs/agnes-image"

    body = {"model": model, "prompt": prompt, "size": size}
    if ratio:
        body["ratio"] = ratio
    if return_base64:
        body["return_base64"] = True
    extras = p.get("extras")
    if isinstance(extras, dict):
        body.update(extras)

    # response_format MUST live in extra_body (top-level breaks the API)
    extra = dict(p.get("extra_body") or {})
    if images:
        extra["image"] = images
    extra.setdefault("response_format", "b64_json" if return_base64 else "url")
    body["extra_body"] = extra

    key = load_key()
    req = urllib.request.Request(
        API,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", "replace")
        except Exception:
            detail = str(e)
        fail(f"API_ERROR: HTTP {e.code} {detail}")
    except Exception as e:
        fail(f"API_ERROR: {e}")

    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    saved = 0
    for i, item in enumerate(resp.get("data") or [], 1):
        if not isinstance(item, dict):
            continue
        path = out / f"agnes-image-{stamp}-{i}.png"
        try:
            if item.get("url"):
                with urllib.request.urlopen(item["url"], timeout=TIMEOUT) as r, open(path, "wb") as f:
                    f.write(r.read())
            elif item.get("b64_json"):
                path.write_bytes(base64.b64decode(item["b64_json"]))
            else:
                continue
        except Exception as e:
            print(f"DOWNLOAD_ERROR: {e}")
            continue
        saved += 1
        print(f"SAVED={path.resolve()}")
    if saved == 0:
        fail(f"NO_IMAGE_IN_RESPONSE: {json.dumps(resp, ensure_ascii=False)[:2000]}")


if __name__ == "__main__":
    main()
