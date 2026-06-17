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

> **定位 ID**：调用方/AI 通常只知道客服名或客户名/手机号，不知道 `csrId` / `contactId`。
> 先用 `GET /openapi/csrs?keyword=张三` 或 `GET /openapi/contacts?keyword=138xxxx` 搜出来拿到 id，
> 再传给其它接口（replies / messages 的 `csrId` / `contactId`）。

---

## 1. 回复明细 `GET /openapi/replies`

数据来源：`tb_wa_message` 中 `direction='outbound'`（已发送的回复）**或** `copilot_accept_mode='REJECTED'` 的 inbound（被拒绝、未发送）。
这样 ACCEPT/MODIFIED/MANUAL 来自 outbound，REJECTED（未发送）来自被拒绝的客户触发消息，互不重复。

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
| sendTime | 回复时间（毫秒；REJECTED 行为客户消息时间） |
| acceptMode | 回复形式：`ACCEPT`=无修改发送 / `MODIFIED`=修改后发送 / `MANUAL`=手动编写 / `REJECTED`=未发送 |
| msgType | 消息类型 |
| direction | `outbound`=已发送回复 / `inbound`=被拒绝的客户触发消息 |
| suggestionContent | 修改前内容（copilot 建议） |
| sentContent | 实际发送内容（REJECTED 行为客户原文，无发送内容） |
| taskUuid | copilot 任务 uuid（可关联同一次 copilot） |

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
| acceptMode | copilot 回复形式（inbound 触发消息与 outbound 回复均带）：ACCEPT/MODIFIED/MANUAL/REJECTED |
| suggestionContent | copilot 建议内容 |
| taskUuid | copilot 任务 uuid |

**指标算法**

- 平均首次回复时长：一个自然日内，每个客户首条 inbound 的 `waitSeconds` 总和 / 已回复单聊数。
- 已回复单聊占比：当天有 inbound 的客户中，`repliedAt` 非空的占比。

---

## 2.5 完整来往消息 `GET /openapi/conversations`

数据来源：`tb_wa_message`，按时间段直接拉取 **inbound + outbound 完整对话流**（含正文 / 媒体 / copilot 痕迹），
按 `contactId` 分组、`send_time` 升序，便于还原一段时间内的完整往来。与 `/openapi/messages` 区别：本接口面向"读对话"，字段更全（含正文、媒体、copilot 痕迹），默认 `size=200`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startTime | long | 是 | 起始毫秒时间戳（按 send_time） |
| endTime | long | 是 | 结束毫秒时间戳（按 send_time） |
| contactId | long | 否 | 客户ID（取单个客户的完整对话） |
| csrId | long | 否 | 客服 |
| direction | string | 否 | `inbound` / `outbound` |
| page / size | int | 否 | 分页（默认 size=200） |

返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| id | 消息ID |
| contactId | 客户ID |
| direction | inbound / outbound |
| msgType | 消息类型 |
| csrId / csrName | 关联客服ID / 名 |
| sendTime | 消息时间（毫秒） |
| textContent | 文本内容 |
| imgLink | 图片链接（如有） |
| acceptMode | copilot 回复形式（ACCEPT/MODIFIED/MANUAL/REJECTED） |
| suggestionContent | copilot 建议内容 |
| taskUuid | copilot 任务 uuid |
| repliedAt | inbound 被回复时间（毫秒） |
| waitSeconds | 首次回复时长（秒） |

---

## 3. 客户明细 `GET /openapi/contacts`

数据来源：`tb_contacts` + `tb_contacts_info` + `tb_csr` + `tb_stage`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| csrId | long | 否 | 分配客服 |
| keyword | string | 否 | 模糊匹配 昵称(nickName)/备注(username)/手机号(phoneNumber) |
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

---

## 4. 客户详情 `GET /openapi/contacts/{id}`

按 contactId 取单个客户，返回字段同上面客户明细的单行（`data` 为对象，非数组）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | long | 是 | 路径参数，客户ID |
| lang | string | 否 | `cn`（默认）/ `en` |

客户不存在时返回 `{ "code": 500203, "msg": "客户不存在" }`。

---

## 5. 客服列表 / 搜索 `GET /openapi/csrs`

数据来源：`tb_csr`，已脱敏（不含密码 / token salt）。用于按名字等定位 `csrId`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 模糊匹配 name/account/phone/email |
| status | int | 否 | 0=禁用 / 1=启用 |
| page / size | int | 否 | 分页 |

返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| id | 客服ID（即各接口的 csrId） |
| account | 登录账号 |
| name | 姓名/昵称 |
| phone | 手机号 |
| email | 邮箱 |
| status | 0=禁用 / 1=启用 |
| isDefault | 是否默认客服 |
| manage | 是否管理员 |
| allowAutopilot | 是否允许 Autopilot |
| wecomUserid / wecomNotify | 企微 userid / 通知开关 |
| feishuUserid / feishuNotify | 飞书 user_id / 通知开关 |
| larkUserid / larkNotify | Lark user_id / 通知开关 |
| remark | 备注 |
| createdAt | 创建时间（毫秒） |

---

## 6. 客服详情 `GET /openapi/csrs/{id}`

按 csrId 取单个客服，返回字段同上面客服列表的单行（`data` 为对象）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | long | 是 | 路径参数，客服ID |

客服不存在时返回 `{ "code": 500203, "msg": "客服不存在" }`。
