# Carcolate-IM OpenAPI 接口文档

## 鉴权

所有接口路径前缀 `/openapi/`，请求头携带：

```
X-Api-Key: <tb_admin_user.api_key>
```

API Key 在后台管理员记录中创建或轮换；管理员被禁用后，该 Key 也不可用。
接口返回的数据沿用该管理员的经销商和可见平台账号范围。

## 通用约定

- 时间入参：**毫秒时间戳**（Long）。
- 时间出参：统一返回**毫秒时间戳**（Long），无值为 `null`。同时附带 `xxxStr` 格式化字段（`yyyy-MM-dd HH:mm`，UTC+8），便于直接展示。
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
| keyword | string | 否 | 模糊匹配 textContent / copilotSuggestion |
| page / size | int | 否 | 分页 |

返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| id | 消息ID |
| contactId | 客户ID |
| nickName | 客户 WA 昵称 |
| username | 客户系统备注 |
| csrId | 回复人ID |
| csrName | 回复人名 |
| sendTime | 回复时间（毫秒；REJECTED 行为客户消息时间） |
| sendTimeStr | sendTime 格式化（`yyyy-MM-dd HH:mm`） |
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
| nickName | 客户 WA 昵称 |
| username | 客户系统备注 |
| direction | inbound / outbound |
| msgType | 消息类型 |
| csrId | 关联客服ID |
| csrName | 客服名 |
| sendTime | 消息时间（毫秒） |
| sendTimeStr | sendTime 格式化（`yyyy-MM-dd HH:mm`） |
| repliedAt | inbound 被回复时间（毫秒），未回复为 null |
| repliedAtStr | repliedAt 格式化（`yyyy-MM-dd HH:mm`） |
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
| nickName | 客户 WA 昵称 |
| username | 客户系统备注 |
| direction | inbound / outbound |
| msgType | 消息类型 |
| csrId / csrName | 关联客服ID / 名 |
| sendTime | 消息时间（毫秒） |
| sendTimeStr | sendTime 格式化（`yyyy-MM-dd HH:mm`） |
| textContent | 文本内容 |
| imgLink | 图片链接（如有） |
| acceptMode | copilot 回复形式（ACCEPT/MODIFIED/MANUAL/REJECTED） |
| suggestionContent | copilot 建议内容 |
| taskUuid | copilot 任务 uuid |
| repliedAt | inbound 被回复时间（毫秒） |
| repliedAtStr | repliedAt 格式化（`yyyy-MM-dd HH:mm`） |
| waitSeconds | 首次回复时长（秒） |

---

## 2.6 标签变更流水 `GET /openapi/stage-logs`

数据来源：`tb_contact_stage_log`。客户跟踪标签(stage)每次变化记一条，便于追踪是哪条消息触发的标签变更。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| contactId | long | 否 | 客户ID |
| startTime | long | 否 | changedAt >= 毫秒时间戳 |
| endTime | long | 否 | changedAt <= 毫秒时间戳 |
| page / size | int | 否 | 分页 |

返回 `data[]` 字段（按 changedAt 倒序）：

| 字段 | 说明 |
|------|------|
| id | 流水ID |
| contactId | 客户ID |
| nickName | 客户 WA 昵称 |
| username | 客户系统备注 |
| messageId | 触发本次变更的消息ID（可能为 null） |
| stageFrom | 变更前标签 stage_key 数组（首次为空数组） |
| stageTo | 变更后标签 stage_key 数组 |
| changedAt | 变更时间（毫秒） |
| changedAtStr | changedAt 格式化（`yyyy-MM-dd HH:mm`） |

---

## 3. 客户明细 `GET /openapi/contacts`

数据来源：`tb_contacts` + `tb_contacts_info` + `tb_csr` + `tb_stage`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| csrId | long | 否 | 分配客服 |
| keyword | string | 否 | 模糊匹配 昵称(nickName)/备注(username)/手机号(phoneNumber) |
| stage | string | 否 | stage_key 过滤，逗号分隔，包含其一即匹配 |
| stageLevel | string | 否 | 按等级过滤（如 `H`/`A`/`B`/`C`/`D`），自动查出该等级下的所有 stageKey 并合并到 stage 过滤 |
| userArea | string | 否 | 国家地区代码，如 CN（精确） |
| linkAccounts | int | 否 | WA 账号 ID（精确） |
| id | long | 否 | 客户ID（精确） |
| nickName | string | 否 | 昵称（模糊） |
| summaryKeyword | string | 否 | 会话总结关键字（模糊） |
| startTime | long | 否 | firstSeen >= 毫秒时间戳 |
| endTime | long | 否 | firstSeen <= 毫秒时间戳 |
| lastSeenStart | long | 否 | lastSeen >= 毫秒时间戳 |
| lastSeenEnd | long | 否 | lastSeen <= 毫秒时间戳 |
| lastSeenAfter | long | 否 | 兼容老入参，等价于 `lastSeenStart` |
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
| dealerId | 归属经销商ID（未绑定为 0） |
| csrName | 分配客服名 |
| linkAccounts | 来源 WA 账号 ID |
| linkAccountLabel | 来源 WA 账号 label（accountName + 手机号） |
| firstSeen | 初次联系时间（毫秒） |
| firstSeenStr | firstSeen 格式化（`yyyy-MM-dd HH:mm`） |
| lastSeen | 最近沟通时间（毫秒） |
| lastSeenStr | lastSeen 格式化（`yyyy-MM-dd HH:mm`） |
| needReply | 状态：1=待回复 / 0=已回复 / -1=无需回复 |
| stages | 跟踪标签对象数组（见下方结构） |
| stageUpdatedAt | 标签更新时间（毫秒） |
| stageUpdatedAtStr | stageUpdatedAt 格式化（`yyyy-MM-dd HH:mm`） |
| tiktokNickname | TikTok 昵称 |
| summaryContent | 会话总结 |
| summaryAt | 总结生成时间（毫秒） |
| summaryAtStr | summaryAt 格式化（`yyyy-MM-dd HH:mm`） |
| source | 客户来源：`Initiative`=主动建联 / `TiktokLeads`=TikTok 留资 / `TiktokMessage`=TikTok 私信 |

`stages[]` 元素结构：

| 字段 | 说明 |
|------|------|
| stageKey | 标签唯一标识 |
| name | 按 `lang` 翻译后的名称 |
| stageLevel | 等级分类（如 `H`/`A`/`B`/`C`/`D`） |

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
| dealerId | 归属经销商ID（未绑定为 0） |
| status | 0=禁用 / 1=启用 |
| isDefault | 是否默认客服 |
| allowAutopilot | 是否允许 Autopilot |
| wecomUserid / wecomNotify | 企微 userid / 通知开关 |
| feishuUserid / feishuNotify | 飞书 user_id / 通知开关 |
| larkUserid / larkNotify | Lark user_id / 通知开关 |
| remark | 备注 |
| createdAt | 创建时间（毫秒） |
| createdAtStr | createdAt 格式化（`yyyy-MM-dd HH:mm`） |

---

## 6. 客服详情 `GET /openapi/csrs/{id}`

按 csrId 取单个客服，返回字段同上面客服列表的单行（`data` 为对象）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | long | 是 | 路径参数，客服ID |

客服不存在时返回 `{ "code": 500203, "msg": "客服不存在" }`。

---

## 7. 客户标签字典 `GET /openapi/stages`

数据来源：`tb_stage`。返回全量标签列表，供调用方做下拉过滤 / 翻译展示。

无请求参数。

返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| stageKey | 标签唯一标识（如 `ice_breaking`） |
| nameCn | 中文名称 |
| nameEn | 英文名称 |
| stageLevel | 等级分类（如 `H`/`A`/`B`/`C`/`D`） |
| sortOrder | 排序权重，数字越小越靠前 |

---

## 8. 回复时效聚合 `GET /openapi/efficiency`

数据来源：`tb_wa_message`。按 **天×客服** 聚合单聊数 / 已回复数 / 首响总秒数，占比与均值由调用方计算。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| csrId | long | 否 | 客服ID |
| startTime | long | 是 | 起始毫秒时间戳 |
| endTime | long | 是 | 结束毫秒时间戳 |
| page / size | int | 否 | 分页（默认 1 / 50） |

返回 `data[]` 字段（按 statDate 倒序、totalChats 倒序）：

| 字段 | 说明 |
|------|------|
| csrId | 客服ID |
| csrName | 客服名 |
| statDate | 统计日期（`YYYY-MM-DD`） |
| totalChats | 单聊数（每客户每天首条 inbound 记 1） |
| repliedChats | 已回复单聊数 |
| totalReplySec | 首响总秒数（可除以 repliedChats 得平均首响） |

**指标算法**

- 平均首次回复时长：`totalReplySec / repliedChats`
- 已回复占比：`repliedChats / totalChats`

---

## 9. DCC看板统计 `GET /openapi/dcc/stats`

数据来源：`tb_wa_message` + `tb_contacts`。一次返回区间汇总（summary）+ 按天趋势（trend），供数据中心看板消费。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startTime | long | 是 | 起始毫秒时间戳 |
| endTime | long | 是 | 结束毫秒时间戳 |

返回 `data` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| summary | object | 汇总统计 |
| trend | array | 按天趋势 |

`summary` 字段：

| 字段 | 说明 |
|------|------|
| totalChats | 单聊数 |
| repliedChats | 已回复单聊数 |
| avgFirstReplySec | 平均首响时长（秒） |
| inboundCount | 收到消息数 |
| outboundCount | 发送消息数 |
| newContacts | 新增客户数 |
| totalContacts | 客户总数 |

`trend[]` 字段：

| 字段 | 说明 |
|------|------|
| day | 日期（`YYYY-MM-DD`） |
| inboundCount | 当天收到消息数 |
| outboundCount | 当天发送消息数 |
| newContacts | 当天新增客户数 |

---

## 10. 客户检索条件分布 `GET /openapi/contacts/distribution`

数据来源：`tb_contacts` + `tb_contacts_info` + `tb_csr` + `tb_stage`。
对 `/openapi/contacts` 同名筛选条件命中的客户集合输出 4 段饼图源数据：跟踪标签 / 归属客服 / 地区 / 待回复状态。**不分页**，命中即整体聚合。

入参与 `/openapi/contacts` 完全一致（`csrId / keyword / stage / userArea / linkAccounts / id / nickName / summaryKeyword / startTime / endTime / lastSeenStart / lastSeenEnd / lastSeenAfter / lang`），不接受 `page / size`。

返回 `data` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| total | int | 命中客户数 |
| stage | array | 按跟踪标签聚合（多标签按出现次数计） |
| csr | array | 按归属客服聚合 |
| area | array | 按 `userArea` 聚合，空值归并到 `UNKNOWN` |
| needReply | array | 按 `needReply` 状态聚合 |

`stage[]` / `needReply[]` 元素：

| 字段 | 说明 |
|------|------|
| key | 原始值（stage_key / needReply 数值；needReply 为 null 表示新客户） |
| name | 按 lang 翻译后的展示名称 |
| count | 命中数 |

`csr[]` 元素：

| 字段 | 说明 |
|------|------|
| id | 分配客服ID（`0`=共享池 / `-1`=抢占未拿 / `null`=未分配） |
| name | 客服展示名（含特殊值翻译） |
| count | 命中数 |

`area[]` 元素：

| 字段 | 说明 |
|------|------|
| key | 国家地区代码（如 `CN`，无值统一为 `UNKNOWN`） |
| count | 命中数 |

---

## 11. 客户接口 `linkAccounts` 语义

`linkAccounts` 用于表示客户当前是否已经建立 WhatsApp 会话：

| 取值 | 含义 |
|------|------|
| `null` 或 `0` | **未建联线索**（导入未发模板 / 等待客户主动联系） |
| `> 0` | 已建联，对应 `tb_wa_accounts.id`，出现在「对话」Tab |

调用方在 `/openapi/contacts` 检索时：
- `linkAccounts=0` 可单独拉取未建联线索。
- 客户主动来 WhatsApp 消息后会自动从 `0` 升级为对应 `wa_account.id`（系统内部由 `ContactsDao#getOrCreateFromPhoneNumber` 完成），调用方无需感知。

---

# V2 多平台接口

V2 按平台拆分路由。路径前缀 `/openapi/v2/`。

## 鉴权与数据范围

所有接口使用管理员记录中的 API Key 鉴权，不再配置独立 API Scope。
接口数据范围沿用该管理员绑定的经销商和可见平台账号。

---

## V2 WhatsApp 接口 `/openapi/v2/whatsapp`

### 平台账号列表 `GET /v2/whatsapp/accounts`

返回当前管理员可见的 WhatsApp 平台账号。

返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| platform | 固定 `whatsapp` |
| platformAccountId | 平台账号ID |
| displayName | 展示名 |
| externalAccountId | 外部账号ID |
| enabled | 是否启用 |
| assignMode | 分配模式 |
| assignCsrId | 指定客服ID |
| legacyWaAccountId | 旧 WA 账号ID |

### 客户列表 `GET /v2/whatsapp/contacts`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| csrId | long | 否 | 分配客服 |
| dealerId | long | 否 | 精确筛选经销商 ID |
| dealerAssigned | boolean | 否 | `true` 只返回已下发线索（已绑定经销商），即 `dealerId > 0` |
| keyword | string | 否 | 模糊匹配昵称/备注/手机号 |
| stage | string | 否 | stageKey 逗号分隔 |
| stageLevel | string | 否 | 按等级过滤（如 `H`/`A`/`B`/`C`/`D`） |
| linkAccounts | int | 否 | WA 账号 ID |
| platformAccountId | long | 否 | 平台账号ID |
| id | long | 否 | 客户ID |
| nickName | string | 否 | 昵称（模糊） |
| userArea | string | 否 | 国家地区代码 |
| summaryKeyword | string | 否 | 会话总结关键字 |
| startTime / endTime | long | 否 | firstSeen 时间区间 |
| lastSeenStart / lastSeenEnd | long | 否 | lastSeen 时间区间 |
| lang | string | 否 | `cn`（默认）/ `en` |
| page / size | int | 否 | 分页，默认 1 / 50 |

返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| platform | 固定 `whatsapp` |
| platformAccountId | 平台账号ID |
| id | 客户ID |
| nickName | WhatsApp 昵称 |
| username | 系统备注 |
| avatar | 头像 |
| phoneNumber | 电话 |
| userArea | 国家地区代码 |
| assignedCsrId | 分配客服ID |
| dealerId | 归属经销商 ID；`0` 或空值表示未下发 |
| csrName | 分配客服名 |
| linkAccounts | 来源 WA 账号 ID |
| linkAccountLabel | 来源 WA 账号标签 |
| platformAccountLabel | 平台账号展示名（有值时才出现） |
| firstSeen / firstSeenStr | 初次联系时间 |
| lastSeen / lastSeenStr | 最近沟通时间 |
| needReply | 1=待回复 / 0=已回复 / -1=无需回复 |
| stages | 标签对象数组 `[{stageKey, name, stageLevel}]` |
| summaryContent | 会话总结 |
| summaryAt / summaryAtStr | 总结时间 |
| source | 客户来源 |

### 客户详情 `GET /v2/whatsapp/contacts/{id}`

按 contactId 取单个客户，返回字段同客户列表单行。

### 消息明细 `GET /v2/whatsapp/messages`

`contactId` **必传**，不分页（一次返回该客户在时间区间内所有消息）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| contactId | long | **是** | 客户ID |
| startTime | long | 是 | 起始毫秒时间戳 |
| endTime | long | 是 | 结束毫秒时间戳 |
| csrId | long | 否 | 客服 |
| direction | string | 否 | `inbound` / `outbound` |
| hasReply | bool | 否 | 仅已回复/未回复的 inbound |
| chatOnly | bool | 否 | 默认 `false`，`true` 时仅返回精简对话字段 |

`chatOnly=false` 返回 `data[]` 字段：

| 字段 | 说明 |
|------|------|
| platform | 固定 `whatsapp` |
| platformAccountId | 平台账号ID |
| id | 消息ID |
| contactId | 客户ID |
| nickName | 客户昵称 |
| username | 客户备注 |
| direction | inbound / outbound |
| msgType | 消息类型 |
| textContent | 文本内容 |
| mediaUrl | 媒体链接 |
| csrId / csrName | 客服ID / 名 |
| sendTime / sendTimeStr | 发送时间 |
| repliedAt / repliedAtStr | 回复时间 |
| repliedByCsrId | 回复客服ID |
| waitSeconds | 首次回复时长（秒） |
| status | 消息状态 |
| externalMessageId | 外部消息ID |
| acceptMode | copilot 回复形式 |
| suggestionContent | copilot 建议 |
| taskUuid | copilot 任务 UUID |

`chatOnly=true` 返回精简字段：

| 字段 | 说明 |
|------|------|
| direction | inbound / outbound |
| textContent | 消息内容 |
| csrName | 客服名 |
| sendTimeStr | 发送时间（`yyyy-MM-dd HH:mm`） |

### 回复明细 `GET /v2/whatsapp/replies`

入参与 V1 `/openapi/replies` 一致，返回字段同消息明细（完整模式）。

### 回复时效 `GET /v2/whatsapp/efficiency`

入参与 V1 `/openapi/efficiency` 一致，返回字段一致。

### 客户分布 `GET /v2/whatsapp/distribution`

入参增加 `stageLevel` 和 `platformAccountId`，返回字段与 V1 `/openapi/contacts/distribution` 一致。

---

## V2 TikTok 接口 `/openapi/v2/tiktok`

接口结构与 V2 WhatsApp **完全一致**，仅路径前缀不同。contacts 返回额外带 `tiktokNickname` 字段；同样支持 `dealerId` 和 `dealerAssigned`，其中已下发定义为 `dealerId > 0`。

---

## V2 通用接口 `/openapi/v2/common`

### 客服列表 `GET /v2/common/csrs`

返回当前管理员可见平台账号范围内绑定的客服。

| 字段 | 说明 |
|------|------|
| id | 客服ID |
| account | 登录账号 |
| name | 姓名 |
| status | 0=禁用 / 1=启用 |

### 标签字典 `GET /v2/common/stages`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| lang | string | 否 | `cn`（默认）/ `en` |

| 字段 | 说明 |
|------|------|
| stageKey | 标签唯一标识 |
| name | 按 lang 翻译后的名称 |
| stageLevel | 等级分类 |
| sortOrder | 排序权重 |

### DCC 统计 `GET /v2/common/dcc/stats`

入参与 V1 `/openapi/dcc/stats` 一致，返回字段一致。
