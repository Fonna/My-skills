#!/usr/bin/env python3
"""抓取 Medium（medium.com / towardsai.net 等）文章正文。

Medium 有 Cloudflare 防护，直连或经机房 IP 访问通常返回 403。
本脚本按「镜像回退链」依次尝试多个 Medium 镜像，返回清洗后的正文。

抓取动作交给 curl：
  - 有 https_proxy / http_proxy 等代理变量 → curl 自己按环境变量走代理
  - 无代理变量但系统装了 proxychains4 → 显式套 proxychains4
（Python 的 urllib 虽认代理变量，但在无代理环境下不如 proxychains 可靠。）

用法：
    python3 fetch_medium_article.py URL
    python3 fetch_medium_article.py URL --format markdown --out article.md
    python3 fetch_medium_article.py URL --json          # 全文 JSON（含 attempts）

退出码：
    0 抓取成功   2 全部镜像失败   3 参数/URL 非法   4 输出写文件失败
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse, parse_qsl, urlencode, urlsplit, urlunsplit

# ─── 配置 ────────────────────────────────────────────────────────────────────

# 镜像回退链：按顺序尝试，第一个拿到有效正文的即采用。
MIRRORS = [
    ("freedium-mirror.cfd", "https://freedium-mirror.cfd/{u}", "Freedium 镜像，正文最完整，优先使用"),
    ("freedium.cfd", "https://freedium.cfd/{u}", "Freedium 备用域名（有时变为停放页，会自动跳过）"),
    ("readmedium.com", "https://readmedium.com/en/{u}", "readmedium（需 JS 渲染，通常抓不到正文，兜底）"),
    ("direct", "{u}", "直连 medium.com（通常被 Cloudflare 拦截，最后尝试）"),
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 90
DEFAULT_MAX_CHARS = 400_000
MIN_BODY_CHARS = 200  # 少于这个长度视为「不是正文」

ALLOWED_HOSTS = {
    "medium.com", "towardsai.net", "pub.towardsai.net",
    "levelup.gitconnected.com", "javascript.plainenglish.io",
    "uxdesign.cc", "hackernoon.com", "codeburst.io", "itnext.io",
    "proandroiddev.com", "infosecwriteups.com", "towardsdatascience.com",
    "machinelearningmastery.com",
}

PROXY_ENV_KEYS = (
    "https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY", "ALL_PROXY", "all_proxy",
)

# 镜像站自身的导航/页脚噪声（只过滤短行，避免误伤正文）。
NOISE_PATTERNS = [
    r"^[·•\->]\s*freedium", r"^freedium", r"^read medium articles", r"^by freedium",
    r"^[🎉🎊]\s*[\d.]+\s*[MK]?$", r"^\d+(\.\d+)?[MK]?\s*(articles?\s*)?unlocked$",
    r"toggle menu", r"^download article$", r"^skip to main content$",
    r"^add$", r"^search⌘k$", r"^library$", r"^feeds$", r"^chat$",
    r"^home$", r"^saved$", r"^highlights$", r"^sources$", r"^books$",
    r"^recent$", r"^view all$", r"^loading recent articles$",
    r"^connect my agent$", r"^sign in$", r"^upgrade$",
    r"^fetching and cleaning your document$",
    r"^keep this page open until your document is ready",
    r"^close-tab saving", r"^coming soon$", r"^tags$", r"^new tag$",
    r"^file$", r"^view$", r"^more$", r"^settings$", r"^feedback$",
    r"^aa$", r"^about$", r"^privacy$", r"^terms$", r"^rss$",
    r"^github$", r"^codeberg$", r"^non-member'?s link",
    r"^made with care\.?$", r"^show all \d+ sections$",
    r"browser extensions", r"paypal\.me", r"ko-fi\.com",
    r"liberapay\.com", r"^discord$", r"articles unlocked",
]
_NOISE_RE = [re.compile(p, re.I) for p in NOISE_PATTERNS]


# ─── URL 处理 ────────────────────────────────────────────────────────────────

def normalize_url(raw: str) -> str:
    """校验并规范化 Medium 系 URL，剥掉 tracking 参数。"""
    u = (raw or "").strip()
    if not u:
        raise ValueError("url 不能为空")
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u

    parts = urlsplit(u)
    host = (parts.hostname or "").lower().removeprefix("www.")
    if not host:
        raise ValueError(f"无法解析 URL: {raw}")
    if host not in ALLOWED_HOSTS and not host.endswith(".medium.com"):
        raise ValueError(
            f"不支持的域名 \"{host}\" —— 本工具只抓 Medium 系出版物"
        )

    # 去掉 utm_/source/sk/r 等 tracking 参数
    kept = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not re.match(r"^(utm_|source$|sk$|r$)", k, re.I)
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), ""))


# ─── 抓取 ────────────────────────────────────────────────────────────────────

def has_proxy_env() -> bool:
    return any(os.environ.get(k) for k in PROXY_ENV_KEYS)


def curl_fetch(url: str, timeout: int) -> str:
    """用 curl 抓取页面；自动决定是否套 proxychains4。"""
    curl_bin = os.environ.get("MEDIUM_FETCH_CURL") or shutil.which("curl") or "curl"
    args = [
        "-sS",  # 静默但保留错误
        "-k",   # 容忍镜像站证书链问题
        "-L",   # 跟随重定向
        "--max-time", str(timeout),
        "-H", f"User-Agent: {UA}",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H", "Accept-Language: en-US,en;q=0.9",
        url,
    ]

    bin_path, final_args = curl_bin, args
    # 有代理变量时 curl 自行处理；没有则显式套 proxychains4。
    if not has_proxy_env():
        pc = shutil.which("proxychains4")
        if pc:
            bin_path = pc
            final_args = ["-q", curl_bin, *args]

    try:
        proc = subprocess.run(
            [bin_path, *final_args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout + 10,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"抓取超时（{timeout}s）: {url}")
    except OSError as e:
        raise RuntimeError(f"无法启动 {bin_path}: {e}")

    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()[:300]
        raise RuntimeError(f"curl 退出码 {proc.returncode}: {err}")
    return proc.stdout.decode("utf-8", "replace")


# ─── HTML → 正文 ─────────────────────────────────────────────────────────────

_DROP_BLOCK = re.compile(
    r"<(script|style|noscript|svg|iframe|form|nav|header|footer)\b[^>]*>.*?</\1>",
    re.I | re.S,
)
_COMMENT = re.compile(r"<!--.*?-->", re.S)

# 属性值里可能含 '>'（Tailwind 任意变体如 class="[&>svg]:px-3"），
# 标签匹配必须「引号感知」，否则 <[^>]+> 会在属性中间的 '>' 处截断，
# 把整段 class 文本漏进正文。
_ATTR = r"""(?:[^>"']|"[^"]*"|'[^']*')*"""
_TAG = re.compile(r"<" + _ATTR + r">")
_DROP_BLOCK = re.compile(
    r"<(script|style|noscript|svg|iframe|form|nav|header|footer)\b" + _ATTR + r">.*?</\1\s*>",
    re.I | re.S,
)
_DROP_BLOCK_MIN = re.compile(
    r"<(script|style|noscript|svg|iframe|form)\b" + _ATTR + r">.*?</\1\s*>",
    re.I | re.S,
)
_BLOCK_END = re.compile(
    r"</(p|div|li|h1|h2|h3|h4|h5|h6|tr|section|blockquote|pre|table|ul|ol|figure|figcaption)>",
    re.I,
)


def html_to_text(page: str) -> str:
    s = _COMMENT.sub("", page)
    s = _DROP_BLOCK.sub("", s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = _BLOCK_END.sub("\n", s)
    s = re.sub(r"<td\b" + _ATTR + r">", " | ", s, flags=re.I)
    s = _TAG.sub("", s)
    s = html_mod.unescape(s)
    s = s.replace("\r", "")
    s = re.sub(r"[ \t\u00a0]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def html_to_markdown(page: str) -> str:
    """轻量 markdown 化：保留标题/列表/代码块结构（best-effort）。"""

    def strip(inner: str) -> str:
        return re.sub(r"\s+", " ", html_mod.unescape(_TAG.sub("", inner))).strip()

    s = _COMMENT.sub("", page)
    s = _DROP_BLOCK_MIN.sub("", s)
    s = re.sub(r"<h([1-6])\b" + _ATTR + r">(.*?)</h\1\s*>",
               lambda m: f"\n{'#' * int(m.group(1))} {strip(m.group(2))}\n",
               s, flags=re.I | re.S)
    s = re.sub(r"<li\b" + _ATTR + r">(.*?)</li\s*>",
               lambda m: f"\n- {strip(m.group(1))}", s, flags=re.I | re.S)
    # 空 <pre>（镜像站 UI 里不少）不产出空代码围栏
    def fence(m: re.Match) -> str:
        code = strip(m.group(1))
        return f"\n```\n{code}\n```\n" if code else ""

    s = re.sub(r"<pre\b" + _ATTR + r">(.*?)</pre\s*>", fence,
               s, flags=re.I | re.S)
    s = re.sub(r"<code\b" + _ATTR + r">(.*?)</code\s*>",
               lambda m: f"`{strip(m.group(1))}`", s, flags=re.I | re.S)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</(p|div|blockquote|tr|section)>", "\n\n", s, flags=re.I)
    s = _TAG.sub("", s)
    s = html_mod.unescape(s)
    s = s.replace("\r", "")
    s = re.sub(r"[ \t\u00a0]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    # 与 text 模式一致地滤掉镜像站导航/页脚噪声行
    return "\n".join(l for l in s.split("\n") if not is_noise(l)).strip()


def is_noise(line: str) -> bool:
    t = line.strip()
    if not t:
        return False
    if len(t) > 120:
        return False  # 只过滤短导航行，避免误伤正文
    return any(p.search(t) for p in _NOISE_RE)


def guess_title(page: str, text: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
    if m:
        t = re.sub(r"\s+", " ", html_mod.unescape(m.group(1))).strip()
        t = re.sub(r"\s*[-|]\s*freedium.*$", "", t, flags=re.I)
        t = re.sub(r"\s*[-|]\s*medium.*$", "", t, flags=re.I)
        if t:
            return t
    for line in [l.strip() for l in text.split("\n")[:12]]:
        if 12 <= len(line) <= 160 and not is_noise(line):
            return line
    return ""


def classify_failure(page: str) -> str | None:
    """返回 None 表示页面看起来是文章；否则返回失败原因码。"""
    t = page.lower()
    if "attention required" in t and "cloudflare" in t:
        return "cloudflare_blocked"
    if "sorry, you have been blocked" in t:
        return "cloudflare_blocked"
    if "performing security verification" in t or "just a moment..." in t:
        return "security_check"
    if "failed to render this page" in t:
        return "mirror_render_failed"
    if "parkingcrew" in t or "parklogic" in t:
        return "mirror_parked"
    # Freedium 文章不存在时 SvelteKit 注入 ARTICLE_NOT_FOUND 载荷，正文几乎为空
    if "article_not_found" in t:
        return "article_not_found"
    if re.search(r"__sveltekit_[a-z0-9_]+\.resolve\(1,\s*\(\)\s*=>\s*\[\{html:null", page, re.I):
        return "article_not_found"
    if len(page.encode("utf-8")) < 20_000:  # 成功抓取通常 >100KB
        return "page_too_small"
    return None


def describe_failure(reason: str, nbytes: int) -> str:
    return {
        "cloudflare_blocked": f"被 Cloudflare 拦截（{nbytes} 字节）—— 镜像/Medium 拒绝了本次请求",
        "security_check": f"命中安全验证页（{nbytes} 字节）—— 重试可能成功",
        "mirror_parked": f"镜像域名已被停放/闲置（{nbytes} 字节）",
        "mirror_render_failed": f"镜像渲染页面失败（{nbytes} 字节）",
        "article_not_found": f"镜像上找不到该文章（{nbytes} 字节）—— URL 可能写错、已删除、付费墙或未被镜像收录",
        "page_too_small": f"页面过小，不像文章正文（{nbytes} 字节）",
    }.get(reason, f"页面已抓取（{nbytes} 字节）但未识别出正文")


def extract_article(page: str) -> tuple[str, str]:
    text = html_to_text(page)
    if not text:
        return "", ""
    title = guess_title(page, text)
    lines = [l for l in text.split("\n") if not is_noise(l)]
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return body, title


def fetch_via_mirrors(url: str, timeout: int) -> dict:
    """依次尝试镜像链，返回首个成功结果；全失败则抛异常。"""
    attempts: list[dict] = []
    last_error: Exception | None = None

    for mirror_id, tpl, note in MIRRORS:
        target = tpl.format(u=url)
        try:
            page = curl_fetch(target, timeout)
            reason = classify_failure(page)
            body, title = extract_article(page) if reason is None else ("", "")
            nbytes = len(page.encode("utf-8"))
            ok = reason is None and len(body) > MIN_BODY_CHARS
            rec = {
                "mirror": mirror_id,
                "url": target,
                "ok": ok,
                "bytes": nbytes,
                "text_length": len(body),
                "note": note,
            }
            if reason:
                rec["reason"] = reason
            attempts.append(rec)
            if ok:
                return {"body": body, "title": title, "html": page,
                        "mirror": mirror_id, "attempts": attempts}
            last_error = RuntimeError(f"{mirror_id}: {describe_failure(reason or '', nbytes)}")
        except Exception as e:  # noqa: BLE001 — 单镜像失败不应中断整条链
            attempts.append({"mirror": mirror_id, "url": target,
                             "ok": False, "error": str(e), "note": note})
            last_error = e

    # 镜像明确说文章不存在时，把这个信息提到最前面，比「全部失败」有用得多。
    not_found = next((a for a in attempts if a.get("reason") == "article_not_found"), None)
    if not_found:
        raise MediumFetchError(
            f"镜像 {not_found['mirror']} 上找不到该文章：URL 可能写错、已删除、"
            f"付费墙或未被镜像收录。原始 URL: {url}", attempts
        )
    raise MediumFetchError(
        f"全部镜像均失败，最后一个错误: {last_error or '未知'}", attempts
    )


class MediumFetchError(RuntimeError):
    def __init__(self, message: str, attempts: list[dict] | None = None):
        super().__init__(message)
        self.attempts = attempts or []


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="抓取 Medium 文章正文（自动经镜像回退链绕过 Cloudflare）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("url", help="Medium 文章完整 URL")
    ap.add_argument("--format", choices=["text", "markdown", "html"], default="text",
                    help="输出格式，默认 text")
    ap.add_argument("--out", help="正文写入该文件（不传则写 stdout）")
    ap.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                    help=f"正文最大字符数，默认 {DEFAULT_MAX_CHARS}")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help=f"单个镜像抓取超时秒数，默认 {DEFAULT_TIMEOUT}")
    ap.add_argument("--json", action="store_true",
                    help="stdout 输出完整 JSON（含 title/mirror_used/attempts）")
    ap.add_argument("--no-attempts", action="store_true",
                    help="JSON 结果中不带 attempts 字段")
    args = ap.parse_args(argv)

    try:
        url = normalize_url(args.url)
    except ValueError as e:
        print(f"[ERR] {e}", file=sys.stderr)
        return 3

    try:
        res = fetch_via_mirrors(url, args.timeout)
    except MediumFetchError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        for a in e.attempts:
            detail = a.get("reason") or a.get("error", "")
            print(f"  - {a['mirror']}: {detail}", file=sys.stderr)
        return 2

    if args.format == "html":
        body = res["html"]
    elif args.format == "markdown":
        body = html_to_markdown(res["html"])
    else:
        body = res["body"]

    truncated = len(body) > args.max_chars
    if truncated:
        body = body[: args.max_chars]

    payload = {
        "url": url,
        "title": res["title"],
        "mirror_used": res["mirror"],
        "char_count": len(body),
        "truncated": truncated,
    }
    if not args.no_attempts:
        payload["attempts"] = res["attempts"]

    # 正文落盘 / 输出。始终用 UTF-8，避免中文经管道乱码。
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(body)
        except OSError as e:
            print(f"[ERR] 写入 {args.out} 失败: {e}", file=sys.stderr)
            return 4
        meta = {**payload, "out": args.out}
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    elif args.json:
        print(json.dumps({**payload, "body": body}, ensure_ascii=False, indent=2))
    else:
        # 元信息走 stderr，正文走 stdout，便于 `... > article.md`
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
