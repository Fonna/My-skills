#!/usr/bin/env node
/**
 * medium-fetch-mcp — 抓取 Medium 文章正文的 MCP server（零 npm 依赖）。
 *
 * 背景：medium.com 有 Cloudflare 防护，直连或经机房代理 IP 访问通常返回 403。
 * 本 server 按「镜像回退链」依次尝试多个 Medium 镜像，返回正文纯文本。
 *
 * 网络说明：本服务器访问境外站点需走 mihomo 代理（127.0.0.1:7890）。
 * Node.js 不读取 http_proxy 环境变量，因此本 server 主动把抓取动作
 * 交给 `curl`，由 curl 按 /etc/profile.d/proxy.sh 的代理变量走代理；
 * 若环境变量缺失，则显式用 proxychains4 包裹 curl。
 *
 * 协议：MCP over stdio（JSON-RPC 2.0，换行分隔）。
 * 只实现客户端必需的最小子集：initialize / tools/list / tools/call / ping。
 */
'use strict';

const { spawn } = require('node:child_process');

const SERVER_NAME = 'medium-fetch';
const SERVER_VERSION = '1.0.0';
const PROTOCOL_VERSION = '2024-11-05';

// ─── 配置 ────────────────────────────────────────────────────────────────────

/** 镜像回退链：按顺序尝试，第一个成功返回非空正文的即采用。 */
const MIRRORS = [
  {
    id: 'freedium-mirror.cfd',
    url: (u) => `https://freedium-mirror.cfd/${u}`,
    note: 'Freedium 镜像，正文最完整，优先使用',
  },
  {
    id: 'freedium.cfd',
    url: (u) => `https://freedium.cfd/${u}`,
    note: 'Freedium 备用域名（有时变为停放页，会自动跳过）',
  },
  {
    id: 'readmedium.com',
    url: (u) => `https://readmedium.com/en/${u}`,
    note: 'readmedium（需 JS 渲染，通常抓不到正文，作为兜底）',
  },
  {
    id: 'direct',
    url: (u) => u,
    note: '直连 medium.com（通常被 Cloudflare 拦截，最后尝试）',
  },
];

const UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';

const FETCH_TIMEOUT_MS = 90_000;
const MAX_OUTPUT_CHARS = 400_000;

// ─── 抓取 ────────────────────────────────────────────────────────────────────

/** 判断是否已配置代理（任一常见代理变量非空即认为需要/已配置）。 */
function hasProxyEnv() {
  return Boolean(
    process.env.https_proxy ||
      process.env.HTTPS_PROXY ||
      process.env.http_proxy ||
      process.env.HTTP_PROXY ||
      process.env.ALL_PROXY ||
      process.env.all_proxy,
  );
}

/** 用 curl 抓取页面；自动决定是否套 proxychains4。 */
function curlFetch(url, timeoutMs = FETCH_TIMEOUT_MS) {
  return new Promise((resolve, reject) => {
    const curlBin = process.env.MEDIUM_FETCH_CURL || 'curl';
    const args = [
      '-sS', // 静默但保留错误
      '-k', // 容忍镜像站证书链问题
      '-L', // 跟随重定向
      '--max-time',
      String(Math.ceil(timeoutMs / 1000)),
      '-H',
      `User-Agent: ${UA}`,
      '-H',
      'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      '-H',
      'Accept-Language: en-US,en;q=0.9',
      url,
    ];

    let bin = curlBin;
    let finalArgs = args;
    // Node 不读 http_proxy；若无代理变量且系统有 proxychains4，则显式包裹。
    if (!hasProxyEnv()) {
      const pc = spawnSyncWhich('proxychains4');
      if (pc) {
        bin = pc;
        finalArgs = ['-q', curlBin, ...args];
      }
    }

    const child = spawn(bin, finalArgs, { stdio: ['ignore', 'pipe', 'pipe'] });
    const chunks = [];
    let errChunks = [];
    let killed = false;
    const timer = setTimeout(() => {
      killed = true;
      child.kill('SIGKILL');
    }, timeoutMs + 5_000);
    timer.unref();

    child.stdout.on('data', (d) => chunks.push(d));
    child.stderr.on('data', (d) => errChunks.push(d));
    child.on('error', (e) => {
      clearTimeout(timer);
      reject(new Error(`spawn ${bin} failed: ${e.message}`));
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      const body = Buffer.concat(chunks).toString('utf8');
      if (killed) return reject(new Error(`fetch timed out after ${timeoutMs}ms`));
      if (code !== 0) {
        const err = Buffer.concat(errChunks).toString('utf8').trim();
        return reject(new Error(`curl exit ${code}: ${err.slice(0, 300)}`));
      }
      resolve(body);
    });
  });
}

/** 同步探测可执行文件路径（避免依赖 which）。 */
function spawnSyncWhich(bin) {
  try {
    const { spawnSync } = require('node:child_process');
    const paths = (process.env.PATH || '').split(':');
    for (const p of paths) {
      if (!p) continue;
      const candidate = `${p.replace(/\/$/, '')}/${bin}`;
      const { accessSync, constants } = require('node:fs');
      try {
        accessSync(candidate, constants.X_OK);
        return candidate;
      } catch {
        /* keep looking */
      }
    }
  } catch {
    /* ignore */
  }
  return null;
}

// ─── HTML → 正文 ─────────────────────────────────────────────────────────────

// 属性值里可能含 '>'（Tailwind 任意变体如 class="[&>svg]:px-3"），
// 标签匹配必须「引号感知」，否则 <[^>]+> 会在属性中间的 '>' 处截断，
// 把整段 class 文本漏进正文。
const ATTR = '(?:[^>"\']|"[^"]*"|\'[^\']*\')*';
const RE_ATTR_BLOCK = new RegExp(
  '<(script|style|noscript|svg|iframe|form|nav|header|footer)\\b' + ATTR + '>[\\s\\S]*?</\\1\\s*>',
  'gi',
);
const RE_ATTR_BLOCK_MIN = new RegExp(
  '<(script|style|noscript|svg|iframe|form)\\b' + ATTR + '>[\\s\\S]*?</\\1\\s*>',
  'gi',
);
const RE_ATTR_TAG = new RegExp('<' + ATTR + '>', 'g');

/** 去掉 script/style/noscript/svg，转块级标签为换行，再剥标签。 */
function htmlToText(html) {
  let s = String(html || '');
  s = s.replace(/<!--[\s\S]*?-->/g, '');
  s = s.replace(RE_ATTR_BLOCK, '');
  s = s.replace(/<br\s*\/?>/gi, '\n');
  s = s.replace(/<\/(p|div|li|h1|h2|h3|h4|h5|h6|tr|section|blockquote|pre|table|ul|ol|figure|figcaption)>/gi, '\n');
  s = s.replace(new RegExp('<td\\b' + ATTR + '>', 'gi'), ' | ');
  s = s.replace(RE_ATTR_TAG, '');
  s = decodeEntities(s);
  // 归一化空白
  s = s.replace(/\r/g, '');
  s = s.replace(/[ \t\u00a0]+/g, ' ');
  s = s.replace(/ *\n */g, '\n');
  s = s.replace(/\n{3,}/g, '\n\n');
  return s.trim();
}

function decodeEntities(s) {
  const named = {
    amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ',
    hellip: '…', mdash: '—', ndash: '–', rsquo: '’',
    lsquo: '‘', ldquo: '“', rdquo: '”', middot: '·',
    bull: '•', copy: '©', reg: '®', trade: '™',
    deg: '°', times: '×', divide: '÷', euro: '€',
    pound: '£', yen: '¥', cent: '¢', sect: '§',
    para: '¶', dagger: '†', permil: '‰', laquo: '«',
    raquo: '»', iexcl: '¡', iquest: '¿', szlig: 'ß',
    agrave: 'à', aacute: 'á', acirc: 'â', atilde: 'ã',
    auml: 'ä', aring: 'å', ccedil: 'ç', egrave: 'è',
    eacute: 'é', ecirc: 'ê', euml: 'ë', igrave: 'ì',
    iacute: 'í', icirc: 'î', iuml: 'ï', ntilde: 'ñ',
    ograve: 'ò', oacute: 'ó', ocirc: 'ô', otilde: 'õ',
    ouml: 'ö', oslash: 'ø', ugrave: 'ù', uacute: 'ú',
    ucirc: 'û', uuml: 'ü', yacute: 'ý', yuml: 'ÿ',
  };
  return s
    .replace(/&#x([0-9a-fA-F]+);/g, (_, h) => safeCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => safeCodePoint(parseInt(d, 10)))
    .replace(/&([a-zA-Z][a-zA-Z0-9]*);/g, (m, name) =>
      Object.prototype.hasOwnProperty.call(named, name) ? named[name] : m,
    );
}

function safeCodePoint(cp) {
  if (!Number.isFinite(cp) || cp < 0 || cp > 0x10ffff) return '';
  try {
    return String.fromCodePoint(cp);
  } catch {
    return '';
  }
}

/** 判断抓回的页面是否真的是文章页（而非停放页/验证页/404 页）。 */
function looksLikeArticle(html) {
  return classifyFailure(html) === undefined;
}

/** 返回 undefined 表示页面看起来是文章；否则返回失败原因码。 */
function classifyFailure(html) {
  const t = html.toLowerCase();
  if (t.includes('attention required') && t.includes('cloudflare')) return 'cloudflare_blocked';
  if (t.includes('sorry, you have been blocked')) return 'cloudflare_blocked';
  if (t.includes('performing security verification')) return 'security_check';
  if (t.includes('just a moment...')) return 'security_check';
  if (t.includes('failed to render this page')) return 'mirror_render_failed';
  if (t.includes('parkingcrew') || t.includes('parklogic')) return 'mirror_parked';
  // Freedium 文章不存在时，SvelteKit 会注入 ARTICLE_NOT_FOUND 载荷且正文几乎为空
  if (/article_not_found/i.test(t)) return 'article_not_found';
  if (/__sveltekit_[a-z0-9_]+\.resolve\(1,\s*\(\)\s*=>\s*\[\{html:null/i.test(html)) {
    return 'article_not_found';
  }
  // 明显过小的页面多半是错误页/占位页（成功抓取通常 >100KB）
  if (Buffer.byteLength(html, 'utf8') < 20_000) return 'page_too_small';
  return undefined;
}

/** 把失败原因码翻译成人类可读的一句话。 */
function describeFailure(html, bytes) {
  const reason = classifyFailure(html);
  switch (reason) {
    case 'cloudflare_blocked':
      return `blocked by Cloudflare (${bytes} bytes) — the mirror/Medium refused this request`;
    case 'security_check':
      return `hit a security verification page (${bytes} bytes) — retry may help`;
    case 'mirror_parked':
      return `mirror domain is parked/unused (${bytes} bytes)`;
    case 'mirror_render_failed':
      return `mirror failed to render the page (${bytes} bytes)`;
    case 'article_not_found':
      return `article not found on this mirror (${bytes} bytes) — URL may be wrong, deleted, paywalled, or unindexed`;
    case 'page_too_small':
      return `page too small to be an article (${bytes} bytes)`;
    default:
      return `page fetched (${bytes} bytes) but no article body detected`;
  }
}

/** 从镜像 HTML 中提取文章主体文本。 */
function extractArticleText(html) {
  const text = htmlToText(html);
  if (!text) return { text: '', title: '' };
  const title = guessTitle(html) || guessTitleFromText(text);
  // 去掉 Freedium/镜像站自身的导航噪声行
  const lines = text.split('\n').filter((l) => !isMirrorNoise(l));
  return { text: lines.join('\n').replace(/\n{3,}/g, '\n\n').trim(), title };
}

const NOISE_PATTERNS = [
  /^[·•\->]\s*freedium/i, /^freedium/i, /^read medium articles/i, /^by freedium/i,
  // 注意 u 标志：🎉 是代理对，不加 u 会被拆成两个码元而匹配不到。
  /^[\u{1F389}\u{1F38A}]\s*[\d.]+\s*[MK]?$/u,
  /^\d+(\.\d+)?[MK]?\s*(articles?\s*)?unlocked$/i,
  /toggle menu/i, /^download article$/i, /^skip to main content$/i,
  /^add$/i, /^search⌘k$/i, /^library$/i, /^feeds$/i, /^chat$/i,
  /^home$/i, /^saved$/i, /^highlights$/i, /^sources$/i, /^books$/i,
  /^recent$/i, /^view all$/i, /^loading recent articles$/i,
  /^connect my agent$/i, /^sign in$/i, /^upgrade$/i,
  /^fetching and cleaning your document$/i,
  /^keep this page open until your document is ready/i,
  /^close-tab saving/i, /^coming soon$/i, /^tags$/i, /^new tag$/i,
  /^file$/i, /^view$/i, /^more$/i, /^settings$/i, /^feedback$/i,
  /^aa$/i, /^about$/i, /^privacy$/i, /^terms$/i, /^rss$/i,
  /^github$/i, /^codeberg$/i, /^non-member'?s link/i,
  /^made with care\.?$/i, /^show all \d+ sections$/i,
  /browser extensions/i, /paypal\.me/i, /ko-fi\.com/i,
  /liberapay\.com/i, /^discord$/i, /articles unlocked/i,
];

function isMirrorNoise(line) {
  const t = line.trim();
  if (!t) return false;
  if (t.length > 120) return false; // 只过滤短导航行，避免误伤正文
  return NOISE_PATTERNS.some((p) => p.test(t));
}

function guessTitle(html) {
  const m = /<title[^>]*>([\s\S]*?)<\/title>/i.exec(html);
  if (!m) return '';
  let t = decodeEntities(m[1]).replace(/\s+/g, ' ').trim();
  t = t.replace(/\s*[-|]\s*freedium.*$/i, '').replace(/\s*[-|]\s*medium.*$/i, '');
  return t.trim();
}

function guessTitleFromText(text) {
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
  for (const l of lines.slice(0, 12)) {
    if (l.length >= 12 && l.length <= 160 && !isMirrorNoise(l)) return l;
  }
  return '';
}

// ─── 工具实现 ────────────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: 'fetch_medium_article',
    description:
      '抓取 Medium（medium.com / towardsai.net 等）文章的正文纯文本。' +
      'Medium 有 Cloudflare 防护，直连通常返回 403；本工具自动按 freedium 镜像回退链抓取，' +
      '返回标题、正文、使用的镜像和尝试记录。',
    inputSchema: {
      type: 'object',
      properties: {
        url: {
          type: 'string',
          description: 'Medium 文章完整 URL，例如 https://medium.com/@user/title-abc123',
        },
        max_chars: {
          type: 'integer',
          description: '正文最大字符数，默认 400000',
          minimum: 1000,
          maximum: 2000000,
        },
        format: {
          type: 'string',
          enum: ['text', 'markdown', 'html'],
          description:
            '返回格式：text=纯文本（默认）；markdown=尽力保留标题/列表/代码块的 markdown；html=原始 HTML',
        },
        include_attempts: {
          type: 'boolean',
          description: '是否在结果中附带每个镜像的尝试记录，默认 true',
        },
      },
      required: ['url'],
      additionalProperties: false,
    },
  },
  {
    name: 'fetch_medium_article_html',
    description:
      '抓取 Medium 文章并返回清洗后的 HTML（保留标题层级、列表、代码块、表格结构）。' +
      '适合需要保留文档结构或自行再解析的场景。',
    inputSchema: {
      type: 'object',
      properties: {
        url: {
          type: 'string',
          description: 'Medium 文章完整 URL',
        },
        max_chars: {
          type: 'integer',
          description: '返回 HTML 最大字符数，默认 400000',
          minimum: 1000,
          maximum: 2000000,
        },
      },
      required: ['url'],
      additionalProperties: false,
    },
  },
];

function normalizeMediumUrl(raw) {
  let u = String(raw || '').trim();
  if (!u) throw new Error('url is required');
  if (!/^https?:\/\//i.test(u)) u = `https://${u}`;
  let parsed;
  try {
    parsed = new URL(u);
  } catch {
    throw new Error(`invalid url: ${raw}`);
  }
  const host = parsed.hostname.toLowerCase().replace(/^www\./, '');
  const allowed = new Set([
    'medium.com',
    'towardsai.net',
    'pub.towardsai.net',
    'levelup.gitconnected.com',
    'javascript.plainenglish.io',
    'uxdesign.cc',
    'hackernoon.com',
    'codeburst.io',
    'itnext.io',
    'proandroiddev.com',
    'infosecwriteups.com',
    'towardsdatascience.com',
    'machinelearningmastery.com',
  ]);
  if (!allowed.has(host)) {
    // 允许子域形式（如 pub.towardsai.net 已列举；这里兜底 *.medium.com）
    if (!/\.medium\.com$/.test(host)) {
      throw new Error(
        `unsupported host "${host}" — this tool only fetches Medium-family publications`,
      );
    }
  }
  // 去掉 tracking 参数，保留干净 URL
  for (const k of [...parsed.searchParams.keys()]) {
    if (/^(utm_|source|sk|r)$/i.test(k)) parsed.searchParams.delete(k);
  }
  return { normalized: parsed.toString(), host };
}

async function fetchViaMirrors(normalizedUrl, opts = {}) {
  const attempts = [];
  let lastError = null;
  for (const mirror of MIRRORS) {
    const target = mirror.url(normalizedUrl);
    const started = Date.now();
    try {
      const html = await curlFetch(target);
      const ok = looksLikeArticle(html);
      const { text, title } = ok ? extractArticleText(html) : { text: '', title: '' };
      const bytes = Buffer.byteLength(html, 'utf8');
      const reason = ok ? undefined : classifyFailure(html);
      attempts.push({
        mirror: mirror.id,
        url: target,
        ok: ok && text.length > 200,
        bytes,
        text_length: text.length,
        elapsed_ms: Date.now() - started,
        note: mirror.note,
        ...(reason ? { reason } : {}),
      });
      if (ok && text.length > 200) {
        return { text, title, html, mirror: mirror.id, attempts };
      }
      lastError = new Error(
        `${mirror.id}: ${describeFailure(html, bytes)}`,
      );
    } catch (e) {
      attempts.push({
        mirror: mirror.id,
        url: target,
        ok: false,
        error: String(e.message || e),
        elapsed_ms: Date.now() - started,
        note: mirror.note,
      });
      lastError = e;
    }
  }
  // 如果某个镜像明确说文章不存在，把这个信息提到最前面，比笼统的
  // "all mirrors failed" 有用得多。
  const notFound = attempts.find((a) => a.reason === 'article_not_found');
  if (notFound) {
    const err = new Error(
      `article not found on ${notFound.mirror}: the URL may be wrong, deleted, ` +
        `paywalled, or not indexed by the mirror. Original: ${normalizedUrl}`,
    );
    err.attempts = attempts;
    throw err;
  }
  const err = new Error(
    `all mirrors failed; last error: ${lastError ? lastError.message : 'unknown'}`,
  );
  err.attempts = attempts;
  throw err;
}

async function handleFetchArticle(args) {
  const { normalized } = normalizeMediumUrl(args.url);
  const maxChars = clampInt(args.max_chars, 1000, 2_000_000, MAX_OUTPUT_CHARS);
  const includeAttempts = args.include_attempts !== false;
  const format = args.format || 'text';

  const res = await fetchViaMirrors(normalized);
  let body;
  if (format === 'html') body = res.html;
  else if (format === 'markdown') body = htmlToMarkdownish(res.html);
  else body = res.text;
  const truncated = body.length > maxChars;
  if (truncated) body = body.slice(0, maxChars);

  const payload = {
    url: normalized,
    title: res.title,
    mirror_used: res.mirror,
    char_count: body.length,
    truncated,
    body,
  };
  if (includeAttempts) payload.attempts = res.attempts;

  return {
    content: [{ type: 'text', text: JSON.stringify(payload, null, 2) }],
    structuredContent: payload,
  };
}

async function handleFetchArticleHtml(args) {
  const { normalized } = normalizeMediumUrl(args.url);
  const maxChars = clampInt(args.max_chars, 1000, 2_000_000, MAX_OUTPUT_CHARS);
  const res = await fetchViaMirrors(normalized);
  let html = res.html;
  const truncated = html.length > maxChars;
  if (truncated) html = html.slice(0, maxChars);
  const payload = {
    url: normalized,
    title: res.title,
    mirror_used: res.mirror,
    char_count: html.length,
    truncated,
    html,
  };
  return {
    content: [{ type: 'text', text: JSON.stringify(payload, null, 2) }],
    structuredContent: payload,
  };
}

function clampInt(v, min, max, dflt) {
  if (v === undefined || v === null) return dflt;
  const n = Number.parseInt(v, 10);
  if (!Number.isFinite(n)) return dflt;
  return Math.min(max, Math.max(min, n));
}

/** 轻量 markdown 化：保留标题/列表/代码块结构（best-effort）。 */
function htmlToMarkdownish(html) {
  const reAttr = (tag, body) =>
    new RegExp('<' + tag + '\\b' + ATTR + '>' + body + '<\\/' + tag + '\\s*>', 'gi');

  let s = String(html || '');
  s = s.replace(/<!--[\s\S]*?-->/g, '');
  s = s.replace(RE_ATTR_BLOCK_MIN, '');
  s = s.replace(reAttr('h([1-6])', '([\\s\\S]*?)<\\/h\\1\\s*>'), (_, lv, inner) =>
    `\n${'#'.repeat(Number(lv))} ${stripTags(inner)}\n`);
  s = s.replace(reAttr('li', '([\\s\\S]*?)'), (_, inner) => `\n- ${stripTags(inner)}`);
  // 空 <pre>（镜像站 UI 里不少）不产出空代码围栏
  s = s.replace(reAttr('pre', '([\\s\\S]*?)'), (_, inner) => {
    const code = decodeEntities(stripTags(inner)).trim();
    return code ? `\n\`\`\`\n${code}\n\`\`\`\n` : '';
  });
  s = s.replace(reAttr('code', '([\\s\\S]*?)'), (_, inner) => `\`${stripTags(inner)}\``);
  s = s.replace(/<br\s*\/?>/gi, '\n');
  s = s.replace(/<\/(p|div|blockquote|tr|section)>/gi, '\n\n');
  s = s.replace(RE_ATTR_TAG, '');
  s = decodeEntities(s);
  s = s.replace(/\r/g, '');
  s = s.replace(/[ \t\u00a0]+/g, ' ');
  s = s.replace(/ *\n */g, '\n');
  s = s.replace(/\n{3,}/g, '\n\n');
  // 与 text 模式一致地滤掉镜像站导航/页脚噪声行
  return s.split('\n').filter((l) => !isMirrorNoise(l)).join('\n').trim();
}

function stripTags(s) {
  return decodeEntities(String(s).replace(RE_ATTR_TAG, '')).replace(/\s+/g, ' ').trim();
}

// ─── JSON-RPC over stdio ─────────────────────────────────────────────────────

let buffer = '';
/** 正在处理中的请求数；stdin 关闭后须等它归零再退出，避免截断 in-flight 抓取。 */
let inFlight = 0;
let stdinEnded = false;

process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  buffer += chunk;
  let idx;
  while ((idx = buffer.indexOf('\n')) >= 0) {
    const line = buffer.slice(0, idx).trim();
    buffer = buffer.slice(idx + 1);
    if (line) trackInFlight(handleLine(line));
  }
});

/**
 * stdin 关闭不代表可以立刻退出：异步的 tools/call 可能还在抓取。
 * 这里只在 in-flight 归零后退出；若 60 秒内仍未归零则强制退出。
 */
process.stdin.on('end', () => {
  stdinEnded = true;
  maybeExit();
});

function maybeExit() {
  if (!stdinEnded || inFlight > 0) return;
  // 给 stdout 一点冲刷时间再退出
  setImmediate(() => process.exit(0));
}

function trackInFlight(promise) {
  inFlight += 1;
  const done = () => {
    inFlight -= 1;
    maybeExit();
  };
  promise.then(done, done);
  return promise;
}

// 兜底：stdin 关闭后即使有请求卡住，也不要永久挂起
let exitGuard = null;
process.stdin.on('end', () => {
  if (exitGuard) return;
  exitGuard = setTimeout(() => process.exit(0), 60_000);
  exitGuard.unref();
});

function send(obj) {
  const s = JSON.stringify(obj);
  process.stdout.write(`${s}\n`);
}

function reply(id, result) {
  send({ jsonrpc: '2.0', id, result });
}

function replyError(id, code, message, data) {
  send({
    jsonrpc: '2.0',
    id,
    error: { code, message, ...(data ? { data } : {}) },
  });
}

async function handleLine(line) {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch {
    return; // 忽略非 JSON 行（日志等）
  }
  if (!msg || typeof msg !== 'object' || msg.jsonrpc !== '2.0') return;

  const { id, method, params } = msg;
  const isNotification = id === undefined || id === null;

  try {
    switch (method) {
      case 'initialize':
        reply(id, {
          protocolVersion: PROTOCOL_VERSION,
          capabilities: { tools: { listChanged: false } },
          serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
          instructions:
            'medium-fetch: 抓取 Medium 文章正文。Medium 直连会被 Cloudflare 拦截，' +
            '本工具自动经 freedium 镜像回退链抓取。输入文章 URL，返回标题与正文。',
        });
        return;

      case 'notifications/initialized':
      case 'initialized':
        return; // 通知，无需回复

      case 'ping':
        if (!isNotification) reply(id, {});
        return;

      case 'tools/list':
        reply(id, { tools: TOOLS });
        return;

      case 'tools/call': {
        const name = params && params.name;
        const args = (params && params.arguments) || {};
        let result;
        if (name === 'fetch_medium_article') result = await handleFetchArticle(args);
        else if (name === 'fetch_medium_article_html') result = await handleFetchArticleHtml(args);
        else {
          replyError(id, -32602, `unknown tool: ${name}`);
          return;
        }
        reply(id, result);
        return;
      }

      case 'resources/list':
        reply(id, { resources: [] });
        return;
      case 'prompts/list':
        reply(id, { prompts: [] });
        return;

      default:
        if (!isNotification) {
          replyError(id, -32601, `method not found: ${method}`);
        }
        return;
    }
  } catch (e) {
    const message = String((e && e.message) || e);
    if (isNotification) {
      process.stderr.write(`medium-fetch: notification ${method} failed: ${message}\n`);
      return;
    }
    // 工具级错误按 MCP 规范以 isError 结果返回更友好；协议级错误用 error
    if (method === 'tools/call') {
      reply(id, {
        content: [{ type: 'text', text: JSON.stringify({ error: message }, null, 2) }],
        isError: true,
      });
    } else {
      replyError(id, -32603, message);
    }
  }
}

// 启动日志（走 stderr，绝不污染 stdout 协议流）
process.stderr.write(
  `medium-fetch-mcp ${SERVER_VERSION} ready (proxy env: ${hasProxyEnv() ? 'yes' : 'no→proxychains4'})\n`,
);
