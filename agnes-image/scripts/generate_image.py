#!/usr/bin/env python3
# Agnes AI image generation (agnes-image-2.5-flash / 2.1-flash) — Linux port of generate_image.ps1
#
# Usage:
#   python3 generate_image.py params.json
#   python3 generate_image.py --prompt "..." [--size 2K] [--ratio 16:9] [--image URL ...] \
#       [--model agnes-image-2.5-flash] [--out-dir outputs/agnes-image] [--b64]
#
# Price self-check (built-in, runs on EVERY invocation unless --skip-free-check):
#   1. Official pricing doc (wiki.agnes-ai.com .../agnes-image-25-flash.md), cached 24h in
#      price_status.json next to this script; any pricing tier > $0 => verdict "paid".
#   2. Gateway billing endpoint /v1/dashboard/billing/usage => real cumulative spend (cents).
#      After generating, spend delta > 0 (while doc said free) => PRICE_ALERT + verdict flips to paid.
#   - verdict "paid"  -> REFUSES to generate (exit 2); pass --allow-paid to override.
#   - verdict "unknown" (doc unreachable) -> warns and proceeds, still watched by usage delta.
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
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://apihub.agnes-ai.com/v1/images/generations"
USAGE_API = "https://apihub.agnes-ai.com/v1/dashboard/billing/usage"
DOC_URL = "https://wiki.agnes-ai.com/en/docs/agnes-image-25-flash.md"
TIMEOUT = 300
CHECK_TIMEOUT = 25
CACHE_TTL = 24 * 3600


def fail(msg, code=1):
    print(msg)
    sys.exit(code)


def skill_dir():
    return pathlib.Path(__file__).resolve().parent.parent


CACHE = skill_dir() / "price_status.json"


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


def http_get(url, key=None, timeout=CHECK_TIMEOUT):
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def fetch_total_usage(key):
    """Real cumulative spend in cents (OpenAI-style billing endpoint). None if unavailable."""
    try:
        data = json.loads(http_get(USAGE_API, key=key))
        v = data.get("total_usage")
        return float(v) if isinstance(v, (int, float)) else None
    except Exception:
        return None


def parse_doc_pricing(text):
    """'free' | 'paid' | 'unknown' from the doc's Pricing table (Current price column)."""
    current_idx = None
    saw_row = False
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        low = [c.lower() for c in cells]
        if "current price" in low:
            current_idx = low.index("current price")
            continue
        if current_idx is None:
            continue
        if all(set(c) <= set("-: ") for c in cells if c):
            continue  # table separator row
        if len(cells) <= current_idx or not any("image" in c.lower() for c in cells):
            continue
        prices = [float(x) for x in re.findall(r"\$\s*([0-9]+(?:\.[0-9]+)?)", cells[current_idx])]
        if not prices:
            continue
        saw_row = True
        if any(p > 0 for p in prices):
            return "paid"
    if saw_row:
        return "free"
    if re.search(r"currently.{0,60}\bfree\b", text, re.I):
        return "free"
    return "unknown"


def write_cache(verdict, usage, note=""):
    try:
        CACHE.write_text(
            json.dumps(
                {
                    "checked_at": time.time(),
                    "checked_at_h": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "doc_verdict": verdict,
                    "total_usage_cents": usage,
                    "note": note,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        pass


def read_cache():
    try:
        if CACHE.is_file():
            return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def price_check(key, force=False):
    """Returns (verdict, usage_now). Doc verdict cached 24h; usage always fetched live."""
    cached = None if force else read_cache()
    if cached and cached.get("doc_verdict") in ("free", "paid", "unknown") \
            and time.time() - cached.get("checked_at", 0) < CACHE_TTL:
        verdict = cached["doc_verdict"]
    else:
        try:
            verdict = parse_doc_pricing(http_get(DOC_URL))
        except Exception:
            verdict = "unknown"
        write_cache(verdict, fetch_total_usage(key))
    return verdict, fetch_total_usage(key)


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
    ap.add_argument("--skip-free-check", action="store_true",
                    help="skip the built-in price self-check")
    ap.add_argument("--refresh-check", action="store_true",
                    help="force re-fetch of the pricing doc (ignore 24h cache)")
    ap.add_argument("--allow-paid", action="store_true",
                    help="generate even when the price check says paid")
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

    key = load_key()

    # ---- price self-check -------------------------------------------------
    baseline = None
    if not args.skip_free_check:
        verdict, baseline = price_check(key, force=args.refresh_check)
        if verdict == "paid" and not args.allow_paid:
            fail(
                "PRICE_CHECK=paid: 官方定价页显示 Agnes 生图已收费（或账单端点显示已在计费）。"
                "已拒绝生成以避免误耗费用：改用火山方舟 byted-ark-seedream-skill，"
                "或确认后加 --allow-paid 强制生成。",
                code=2,
            )
        elif verdict == "paid":
            print("PRICE_CHECK=paid (--allow-paid): 继续生成，注意会产生费用")
        elif verdict == "unknown":
            print("PRICE_CHECK=unknown: 定价页不可达，按账单端点实测盯防后继续")
        else:
            u = "n/a" if baseline is None else f"{baseline:g}¢"
            print(f"PRICE_CHECK=free (usage so far: {u})")

    # ---- build request ----------------------------------------------------
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

    # ---- save images -------------------------------------------------------
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

    # ---- post-generation billing watch ------------------------------------
    if not args.skip_free_check and baseline is not None:
        after = fetch_total_usage(key)
        if after is not None and after > baseline:
            print(
                f"PRICE_ALERT: 官方文档称免费但账单出现增量（{baseline:g}¢ -> {after:g}¢），"
                f"已将缓存状态标为 paid；下次调用将被拦截，需 --allow-paid。请转告用户。"
            )
            write_cache("paid", after, note="usage delta while doc said free")


if __name__ == "__main__":
    main()
