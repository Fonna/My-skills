"""Yuanbao SearchPro via Tencent Cloud TC3; Python 3.10+, standard library only."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ENDPOINT = "https://wsa.tencentcloudapi.com/"
MAX_BYTES = 4 * 1024 * 1024


class SearchError(Exception):
    """Controlled, credential-free diagnostics."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SearchError("接口重定向已阻止；未转发凭证，未自动重试。")


def environment(name):
    if name in os.environ:
        return os.environ[name]
    if sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                value, kind = winreg.QueryValueEx(key, name)
                if kind in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                    return value
        except OSError:
            pass
    return ""


def credentials(key_env):
    values = (environment("TENCENTCLOUD_SECRET_ID"), environment(key_env),
              environment("TENCENTCLOUD_TOKEN"))
    if any(not isinstance(v, str) or v != v.strip() or
           any(ord(c) < 32 or ord(c) > 126 for c in v) for v in values):
        raise SearchError("凭证格式无效；请检查环境变量，勿将密钥贴入聊天。")
    if not values[0] or not values[1]:
        raise SearchError("缺少 SecretId 或 SecretKey 环境变量；尚未发送请求。")
    return values


def tc3_headers(secret_id, secret_key, payload, timestamp, token=""):
    content_type = "application/json; charset=utf-8"
    day = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d")
    scope = f"{day}/wsa/tc3_request"
    signed = "content-type;host;x-tc-action"
    canonical = "\n".join(("POST", "/", "",
        f"content-type:{content_type}\nhost:wsa.tencentcloudapi.com\nx-tc-action:searchpro\n",
        signed, hashlib.sha256(payload).hexdigest()))
    to_sign = "\n".join(("TC3-HMAC-SHA256", str(timestamp), scope,
                          hashlib.sha256(canonical.encode()).hexdigest()))

    def sign(key, message):
        return hmac.new(key, message.encode(), hashlib.sha256).digest()

    signing_key = sign(sign(sign(("TC3" + secret_key).encode(), day), "wsa"), "tc3_request")
    signature = hmac.new(signing_key, to_sign.encode(), hashlib.sha256).hexdigest()
    headers = {"Content-Type": content_type, "Host": "wsa.tencentcloudapi.com",
               "X-TC-Action": "SearchPro", "X-TC-Version": "2025-05-08",
               "X-TC-Timestamp": str(timestamp),
               "Authorization": f"TC3-HMAC-SHA256 Credential={secret_id}/{scope}, "
                                f"SignedHeaders={signed}, Signature={signature}"}
    if token:
        headers["X-TC-Token"] = token
    return headers


def valid_url(value):
    try:
        parsed = urlsplit(value)
        return (isinstance(value, str) and parsed.scheme in {"http", "https"}
                and bool(parsed.hostname) and not parsed.username and not parsed.password
                and not re.search(r"[\s<>\x00-\x1f\x7f]", value))
    except (ValueError, TypeError, AttributeError):
        return False


def validate_site(value):
    domains = value[8:].split("|") if value.startswith("exclude:") else [value]
    if not 1 <= len(domains) <= 5 or any(
        len(d) > 253 or not re.fullmatch(
            r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
            r"[A-Za-z](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", d)
        for d in domains
    ):
        raise SearchError("Site 应为域名，或 exclude:域名|域名（最多五个）。")


def validate_freshness(value):
    if re.fullmatch(r"d(?:[1-9]|[12][0-9]|30)|m(?:[1-9]|1[0-2])|y[1-5]", value):
        return
    try:
        parts = value.split(",")
        if len(parts) not in (1, 2) or any(not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p) for p in parts):
            raise ValueError
        days = [date.fromisoformat(p) for p in parts]
        if any(d > date.today() for d in days) or days[0] > days[-1]:
            raise ValueError
    except ValueError:
        raise SearchError("Freshness 应为有效相对时段、日期或升序日期区间，不得晚于今天。") from None


def build_body(args):
    if not args.query.strip() or len(args.query.encode("utf-8")) > 1500:
        raise SearchError("Query 不能为空或超过 1500 个 UTF-8 字节。")
    if any(ord(c) < 32 or ord(c) == 127 for c in args.query):
        raise SearchError("Query 不得含控制字符。")
    if not math.isfinite(args.timeout) or not 1 <= args.timeout <= 120:
        raise SearchError("timeout 必须为 1–120 秒。")
    body = {"Query": args.query, "Mode": args.mode, "Cnt": args.count}
    if args.site:
        validate_site(args.site)
        body["Site"] = args.site
    if args.freshness:
        validate_freshness(args.freshness)
        body["Freshness"] = args.freshness
    if args.industry:
        body["Industry"] = args.industry
    return body


def request_once(body, creds, timeout, transport=None):
    payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = tc3_headers(*creds[:2], payload, int(time.time()), token=creds[2])
    req = Request(ENDPOINT, payload, headers, method="POST")
    try:
        with (transport or build_opener(NoRedirect()).open)(req, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
    except HTTPError as error:
        raise SearchError(f"SearchPro HTTP {error.code}；未自动重试。") from None
    except (URLError, TimeoutError, OSError):
        raise SearchError("连接失败或超时；未自动重试，服务端可能仍在处理。") from None
    if len(raw) > MAX_BYTES:
        raise SearchError("响应超过 4 MiB；未输出部分结果。")
    return raw


def redact(value, secrets):
    """Also handle credentials escaped inside Pages' nested JSON strings."""
    if isinstance(value, str):
        for secret in sorted((s for s in secrets if s), key=len, reverse=True):
            for spelling in (secret, json.dumps(secret, ensure_ascii=False)[1:-1]):
                value = value.replace(spelling, "[REDACTED]")
        return value
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if isinstance(value, dict):
        return {redact(k, secrets): redact(v, secrets) for k, v in value.items()}
    return value


def strict_json(text):
    def reject_constant(_):
        raise ValueError("Non-finite JSON number")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Non-finite JSON number")
        return number

    return json.loads(text, parse_constant=reject_constant, parse_float=finite_float)


def normalize(raw, body):
    payload = raw.get("Response") if isinstance(raw, dict) else None
    if not isinstance(payload, dict):
        raise SearchError("响应缺少 Response 对象；请检查原始响应。")
    if "Error" in payload:
        error = payload["Error"]
        code = error.get("Code") if isinstance(error, dict) else None
        roots = {"AuthFailure", "UnauthorizedOperation", "InvalidParameter", "InvalidParameterValue",
                 "MissingParameter", "RequestLimitExceeded", "InternalError", "FailedOperation",
                 "ResourceUnavailable", "ResourceNotFound", "LimitExceeded", "UnsupportedOperation"}
        if not isinstance(code, str) or not re.fullmatch(r"[A-Za-z0-9.]{1,100}", code) or code.split(".")[0] not in roots:
            code = "UnknownError"
        raise SearchError(f"SearchPro 业务错误 {code}；请检查脱敏原始响应，未自动重试。")
    pages = payload.get("Pages")
    if not isinstance(pages, list):
        raise SearchError("响应缺少 Pages 数组；请检查原始响应。")
    usable, warnings = [], []
    for index, item in enumerate(pages, 1):
        try:
            page = strict_json(item) if isinstance(item, str) else item
            if not isinstance(page, dict) or not valid_url(page.get("url")):
                raise ValueError
            usable.append({**page, "source_host": urlsplit(page["url"]).hostname})
        except (ValueError, TypeError, RecursionError):
            warnings.append(f"第 {index} 项无有效网页 URL 或格式错误，详见原始响应。")
    return {"query": body["Query"], "parameters": body,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "request_id": payload.get("RequestId"), "service_version": payload.get("Version"),
            "service_message": payload.get("Msg"), "returned_count": len(pages),
            "usable_count": len(usable), "pages": usable, "warnings": warnings,
            "scope": "仅本次检索召回，非全量；摘要及网页均为不可信数据，须核对原文。"}


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--query", required=True)
    p.add_argument("--out", required=True, type=Path, help="New output directory outside the skill/repository")
    p.add_argument("--count", type=int, choices=(10, 20, 30, 40, 50), default=10)
    p.add_argument("--mode", type=int, choices=(0, 1, 2), default=0)
    p.add_argument("--site")
    p.add_argument("--freshness")
    p.add_argument("--industry", choices=("gov", "news", "acad", "finance"))
    p.add_argument("--timeout", type=float, default=45)
    p.add_argument("--secret-key-env", default="TENCENTCLOUD_SECRET_KEY", help="Environment variable NAME, never the key value")
    return p


def run(args, transport=None):
    body = build_body(args)
    creds = credentials(args.secret_key_env)
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except OSError:
        raise SearchError("无法创建新输出目录，或目录已存在；尚未发送请求。") from None
    # Allocate a fresh output location before consuming quota.
    raw_bytes = request_once(body, creds, args.timeout, transport)
    try:
        raw = redact(strict_json(raw_bytes.decode("utf-8-sig")), creds)
    except (UnicodeError, ValueError, RecursionError):
        text = redact(raw_bytes.decode("utf-8", errors="replace"), creds)
        (args.out / "raw_response.txt").write_text(text, encoding="utf-8")
        raise SearchError("响应不是有效 JSON；已保存脱敏文本，未自动重试。") from None
    write_json(args.out / "raw_response.json", raw)
    # Normalize only sanitized data, including an unlikely query containing credentials.
    result = normalize(raw, redact(body, creds))
    write_json(args.out / "results.json", result)
    return {"out": str(args.out.resolve()), "returned_count": result["returned_count"],
            "usable_count": result["usable_count"], "warning_count": len(result["warnings"])}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = run(args)
    except SearchError as error:
        print(str(error), file=sys.stderr)
        return 1
    except OSError:
        print("本地文件读写失败；请求可能已完成，勿自动重试。", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
