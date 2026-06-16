# Carcolate-IM OpenAPI 接口文档

## 鉴权

所有接口路径前缀 `/openapi/`，请求头携带：

```
X-Api-Key: <tb_openapi_key.api_key>
```

key 无效或被禁用返回 `{ "code": 500203, "msg": "无效的 API Key" }`。

## 通用约定

- 时间入参：**毫秒时间戳**（Long）。
- 时间出参：统一返回**毫秒时间戳**（Long），无值为 `null`。
- 返回结构（后端统一 `Rsp`）：

```json
{ "code": 0, "msg": null, "data": [ ... ], "total": 123 }
```

- 分页：`page`（默认 1）、`size`（默认 50）；`total` 为符合条件的总数。

---

## 1. 回复明细 `GET /openapi/replies`

数据来源：`tb_wa_message` 中 `direction='outbound'`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startTime | long | 是 | 起始毫秒时间戳（按 send_time） |
| endTime | long | 是 | 结束毫秒时间戳（按 send_time） |
| csrId | long | 否 | 回复人 |
| acceptMode | string | 否 | copilot_accept_mode 过滤，逗号分隔，如 `ACCEPT,MODIFIED` |
| contactId | long | 否 | 客户ID |
| page / size | int | 否 | 分页 |

返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| id | 消息ID |
| contactId | 客户ID |
| csrId | 回复人ID |
| csrName | 回复人名 |
| sendTime | 回复时间（毫秒） |
| acceptMode | 回复形式：`ACCEPT`=无修改发送 / `MODIFIED`=修改后发送 / `MANUAL`=手动编写 / `REJECTED`=未发送 |
| msgType | 消息类型 |
| suggestionContent | 修改前内容（copilot 建议） |
| sentContent | 修改后实际发送内容 |

---

## 2. 消息明细 `GET /openapi/messages`

数据来源：`tb_wa_message` 原始明细（不聚合，供调用方计算回复时效）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startTime | long | 是 | 起始毫秒时间戳（按 send_time） |
| endTime | long | 是 | 结束毫秒时间戳（按 send_time） |
| csrId | long | 否 | 客服 |
| contactId | long | 否 | 客户ID |
| direction | string | 否 | `inbound` / `outbound` |
| hasReply | bool | 否 | true/false：仅返回已回复/未回复的 inbound（设置后强制 direction=inbound） |
| page / size | int | 否 | 分页 |

返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| id | 消息ID |
| contactId | 客户ID |
| direction | inbound / outbound |
| msgType | 消息类型 |
| csrId | 关联客服ID |
| csrName | 客服名 |
| sendTime | 消息时间（毫秒） |
| repliedAt | inbound 被回复时间（毫秒），未回复为 null |
| repliedByCsrId | 回复该 inbound 的客服ID |
| waitSeconds | 首次回复时长（秒）= repliedAt - sendTime |
| textContent | 文本内容 |

**指标算法**

- 平均首次回复时长：一个自然日内，每个客户首条 inbound 的 `waitSeconds` 总和 / 已回复单聊数。
- 已回复单聊占比：当天有 inbound 的客户中，`repliedAt` 非空的占比。

---

## 3. 客户明细 `GET /openapi/contacts`

数据来源：`tb_contacts` + `tb_contacts_info` + `tb_csr` + `tb_stage`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| csrId | long | 否 | 分配客服 |
| stage | string | 否 | stage_key 过滤，逗号分隔，包含其一即匹配 |
| userArea | string | 否 | 国家地区代码，如 CN |
| startTime | long | 否 | firstSeen >= 毫秒时间戳 |
| endTime | long | 否 | firstSeen <= 毫秒时间戳 |
| lastSeenAfter | long | 否 | lastSeen >= 毫秒时间戳 |
| lang | string | 否 | `cn`（默认）/ `en`，影响 stageNames |
| page / size | int | 否 | 分页 |

返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| id | 客户ID |
| nickName | WA 昵称 |
| username | 系统备注 |
| phoneNumber | 电话 |
| userArea | 国家地区代码 |
| assignedCsrId | 分配客服ID |
| csrName | 分配客服名 |
| firstSeen | 初次联系时间（毫秒） |
| lastSeen | 最近沟通时间（毫秒） |
| needReply | 状态：1=待回复 / 0=已回复 / -1=无需回复 |
| stage | 跟踪标签 stage_key 数组 |
| stageNames | 标签按 lang 翻译后的名称数组 |
| stageUpdatedAt | 标签更新时间（毫秒） |
| tiktokNickname | TikTok 昵称 |
| summaryContent | 会话总结 |
| summaryAt | 总结生成时间（毫秒） |
