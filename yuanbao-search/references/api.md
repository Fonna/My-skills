# SearchPro 接口契约

核对日期：2026-11-02。脚本仅实现腾讯云 API 3.0 的 TC3 签名路线。

- POST `https://wsa.tencentcloudapi.com/`
- Service：`wsa`；Action：`SearchPro`；Version：`2025-05-08`。不传 Region。
- Content-Type：`application/json; charset=utf-8`。
- 签名使用实际发送的 UTF-8 字节，UTC 日期，SignedHeaders 为 `content-type;host;x-tc-action`；规范头中的 action 为小写 `searchpro`。
- SecretId、SecretKey 对应腾讯云访问密钥。临时凭证还需 `X-TC-Token`。
- 请求字段：`Query`（必填）、`Mode`、`Cnt`、`Site`、`Freshness`、`Industry`。本技能不实现旗舰版专有参数。
- 响应通常为 `Response.Pages` 数组，条目可能是 JSON 字符串；保留 `RequestId`、`Version`、`Msg`。`Response.Error` 是业务错误，即便 HTTP 为 200 也不能视为成功。
- 日期区间采用官方示例的起日、止日顺序。文档文字对起止顺序存在矛盾；收到日期参数错误时先核对服务最新文档，不能静默反转或自动重试。

官方资料：

- [请求结构](https://cloud.tencent.com/document/product/1806/121814)
- [公共参数](https://cloud.tencent.com/document/product/1806/121815)
- [SearchPro 参数与响应](https://cloud.tencent.com/document/api/1806/121811)
- [腾讯云 API 3.0 签名 v3](https://cloud.tencent.com/document/api/213/30654)
- [独立服务 API Key 接口](https://cloud.tencent.com/document/product/1806/130615)：属于另一种凭证路线，本技能不实现，不把 SecretKey 直接传入 Bearer。
