---
name: agnes-image
description: 默认生图技能:用 Agnes AI(agnes-ai.com,OpenAI 兼容网关,当前限免 $0)生成图片——文生图/图生图/多图合成(agnes-image-2.5-flash)。未指定平台的文生图、画图请求默认走本 skill(为省火山方舟 AgentPlan 额度);脚本每次调用内置价格自检,检测到收费自动拦截(exit 2)。Use when 用户要求生图、画一张图、改图、多图合成,或点名 Agnes。Seedream 仅用于:用户点名火山方舟/Seedream、本 skill 被价格自检拦截且用户不愿 --allow-paid、或需要 Seedream 独有能力(图层拆分/精准交互编辑)。Linux 服务器(DSH)用 scripts/generate_image.py,Windows 用 scripts/generate_image.ps1。需要 AGNES_API_KEY,产物下载到本地。
---

# Agnes AI 图片生成

通过 Agnes AI 网关 `https://apihub.agnes-ai.com/v1` 调用 `agnes-image-2.5-flash`,同步返回 URL → 下载到本地。当前官方限免:$0/张(挂牌价 1K $0.01 / 2K $0.018 / 3K $0.021 / 4K $0.024,第 4 张起参考图 $0.003)。

两个脚本行为一致,按机器选其一:

- **Linux / DSH 服务器**: `scripts/generate_image.py`(Python 3,零依赖)。技能装在 DSH 时目录为 `/root/.agents/skills/agnes-image/`。**内置价格自检**(仅此版有)
- **Windows**: `scripts/generate_image.ps1`(PowerShell)。技能装在 `~/.workbuddy/skills/agnes-image/` 或 `~/.minimax/skills/agnes-image/` 时同理。无自检,Windows 端使用前手动确认限免仍有效

## 默认路由(重要)

- **未指定平台的生图请求默认走本 skill**(文生图、图生图、多图合成都算),目的是省火山方舟 AgentPlan 额度——Agnes 当前限免 $0/张。
- 改用 **byted-ark-seedream-skill** 的条件(仅其一):
  1. 用户点名火山方舟 / Seedream / AgentPlan;
  2. 本 skill 价格自检拦截(exit 2)且用户不愿 `--allow-paid`;
  3. 需要 Seedream 独有能力:图层拆分、精准交互编辑。
- 需要持续出大量图时,先跑一次 `--refresh-check` 确认限免状态再批量。

## 价格自检(内置,每次调用自动执行)

脚本每次运行自动确认是否仍免费,双层判据:

1. **官方定价文档**(24h 缓存于脚本旁 `price_status.json`):解析 Pricing 表格 Current price 列,任一档位 > $0 即判 paid;
2. **网关账单端点** `/v1/dashboard/billing/usage`(每次现查):真实累计消费(美分)。**生成后若出现增量**(文档称免费但实际扣费)→ 打印 `PRICE_ALERT` 并把缓存标为 paid,下次调用直接拦截。

输出行解读:

| 输出 | 含义 | 动作 |
| --- | --- | --- |
| `PRICE_CHECK=free (usage so far: 0¢)` | 限免有效 | 正常出图 |
| `PRICE_CHECK=paid` + exit 2 | 已收费/已计费 | **不生成**。转告用户:改用 Seedream,或用户确认后加 `--allow-paid` |
| `PRICE_CHECK=unknown` | 定价页不可达 | 警告后继续,仍由账单增量盯防 |
| `PRICE_ALERT: ...usage 增量...` | 官方说免费但实际扣费 | 本次已出图,转告用户并改用 Seedream |

CLI 开关:`--skip-free-check` 跳过自检;`--refresh-check` 强制重抓定价页(忽略 24h 缓存);`--allow-paid` 明确放行收费生成。

## 前提检查(每次使用前)

1. 确认 Key 可用:
   - Linux/DSH: `[ -s ~/.config/dsh-secrets/agnes-api-key ] && echo ok || echo missing`(或存在环境变量 `AGNES_API_KEY`)
   - Windows: `if ($env:AGNES_API_KEY) { "ok" } else { "missing" }`
2. 若缺失,**让用户自己在他的终端窗口**配置,配置后重开会话/终端再试:
   - Linux 服务器(DSH): `echo -n '他的Key' > ~/.config/dsh-secrets/agnes-api-key && chmod 600 ~/.config/dsh-secrets/agnes-api-key`
   - Windows: `setx AGNES_API_KEY "他的Key"`
   (Key 从 platform.agnes-ai.com 控制台获取)。**禁止**用户把 Key 粘贴到对话、参数或日志里;脚本只从文件/环境变量读取,绝不回显。
3. 注意区分 Key:本 skill 只认 **AGNES_API_KEY**;ARK_API_KEY / AGENT_API_KEY 是火山方舟的,不能混用。

## 快速开始

中文提示词一律走 JSON 参数文件(UTF-8)或 Linux 命令行参数(Windows 命令行有编码问题,勿直接传中文);生图建议先把中文提示词译成英文(更稳定):

### Linux / DSH(Python 脚本)

单张最简调用(命令行参数直接传):

```bash
python3 /root/.agents/skills/agnes-image/scripts/generate_image.py \
  --prompt "A luminous floating city above a misty canyon at sunrise, cinematic realism, wide-angle composition, rich architectural details, soft golden light" \
  --size 2K --ratio 16:9
```

复杂参数用 JSON 参数文件(在工作目录写 `params.json`):

```json
{
  "prompt": "A luminous floating city above a misty canyon at sunrise, cinematic realism",
  "size": "2K",
  "ratio": "16:9"
}
```

```bash
cd 工作目录 && python3 /root/.agents/skills/agnes-image/scripts/generate_image.py params.json
```

### Windows(PowerShell,原版)

1. 在工作目录写 `params.json`(字段同下方参数说明)
2. 运行:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\generate_image.ps1" -Json params.json
   ```

### 输出

每张图输出一行 `SAVED=<绝对路径>`,默认保存到当前目录 `outputs/agnes-image/`(此前会有 `PRICE_CHECK=...` 行)。完成后把文件交付给用户(DSH 网页会话:用 read_image 预览、present 出文件卡片;文件落在工作区内即可直接打开)。

### 图生图 / 多图合成

```json
{
  "prompt": "Turn the scene into a rain-soaked cyberpunk night with neon reflections while preserving the original composition",
  "image": ["https://example.com/input.png"],
  "size": "2K",
  "ratio": "16:9"
}
```

CLI 传参考图: `--image "https://example.com/input.png"`(可重复传多张)。

参考图放 `image` 数组(公网 URL 或 `data:image/png;base64,...` Data URI);本地图片先上传图床或转 Data URI。多张即多图合成,无需任何 tags。

## 参数说明(JSON 字段)

| 字段 | 默认 | 说明 | CLI 对应 |
| --- | --- | --- | --- |
| prompt | 必填 | 生图/改图提示词 | `--prompt` |
| model | agnes-image-2.5-flash | 也可用 agnes-image-2.1-flash(参数相同) | `--model` |
| size | 2K | 推荐 1K / 2K / 3K / 4K;精确像素如 1024x768 也可但不支持的会被归一化 | `--size` |
| ratio | 服务端默认 1:1 | 1:1 / 3:4 / 4:3 / 16:9 / 9:16 / 2:3 / 3:2 / 21:9,与 size 搭配 | `--ratio` |
| image | 空 | 参考图 URL/Data URI 数组(图生图、多图合成) | `--image`(可重复) |
| return_base64 | false | true 时返回 b64_json,脚本解码保存 | `--b64` |
| out_dir | outputs/agnes-image | 保存目录 | `--out-dir` |
| extras | 空 | 透传进请求体的其他字段对象 | 仅 JSON 模式 |

常用尺寸(官方 Output Dimension Reference):16:9 1K=1312x736、16:9 2K=2624x1472、9:16 2K=1472x2624、1:1 2K=2048x2048。1920x1080/2560x1440 不是模型原生输出,要近似 16:9 画布请请求 `size:"2K"+ratio:"16:9"` 后自行裁剪。

## 关键坑

- 生图接口没有 `n` 参数,单次请求返回一张图(`data[]` 通常 1 项);要多张就多次调用脚本。
- `response_format` **必须放 `extra_body.response_format`,放顶层会报错**(两个脚本均已处理,手写请求时注意)。
- 图生图**不需要** `tags:["img2img"]`,只需 `extra_body.image`。
- 参考图 URL 必须公网可访问(无登录/cookie);取不到时改 Data URI。
- 官方建议客户端超时 60–360 秒,脚本设 300 秒。
- Windows 命令行直接传中文提示词有编码问题,务必走 JSON 文件;Linux 命令行/JSON 均无问题。

## 接口速查(脚本失败时手动排查)

- `POST https://apihub.agnes-ai.com/v1/images/generations`,鉴权 `Authorization: Bearer $AGNES_API_KEY`
- body: `{model, prompt, size, ratio?, extra_body:{image?, response_format}}`(t2i base64 用顶层 `return_base64:true`)
- 返回: `data[].url` 或 `data[].b64_json`
- 账单: `GET /v1/dashboard/billing/usage` → `{"total_usage": <美分>}`(价格自检用它做实测盯防)
- 400=参数错误(重点查 response_format 位置、缺 size)、401=Key 无效、402/欠费=已收费、429=限频退避重试、500/503=稍后重试

## 失败处理

- 脚本 exit 1 时打印 API 错误 JSON(错误码:`MISSING_KEY` / `PARAMS_NOT_FOUND` / `BAD_JSON` / `MISSING_PROMPT` / `API_ERROR` / `DOWNLOAD_ERROR` / `NO_IMAGE_IN_RESPONSE`):如实报告错误信息,**不要盲目重试**;内容审核被拒时让用户改提示词。
- **exit 2 = 价格自检拦截**(`PRICE_CHECK=paid`):不要重试、不要加 `--allow-paid`,直接转告用户并按"默认路由"切 Seedream;只有用户明确同意付费才用 `--allow-paid`。
- API 返回 402/欠费/计费相关错误时,视同收费:删除/忽略 `price_status.json` 缓存,转告用户,改用 Seedream。
- 限免价随时可能调整,批量生成前用 `--refresh-check` 再确认一次。

## 参考

- 模型文档(定价以页内 Pricing 表为准): https://wiki.agnes-ai.com/en/docs/agnes-image-25-flash (每页可加 `.md` 取纯文本)
- 平台/取 Key: https://platform.agnes-ai.com/ ;总览: https://agnes-ai.com/doc/overview
