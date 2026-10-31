---

## name: im-cli
description: 通过命令行查询 Carcolate-IM V2 OpenAPI（客户 / 消息 / 回复 / 标签 / 客服 / 效率）。支持 WhatsApp 和 TikTok 双平台。当需要按时间段、按客服、按客户、按标签拉取 IM 业务数据做统计分析或还原完整对话时使用。

# im-cli

对接 Carcolate-IM V2 OpenAPI 的 CLI 工具，支持 WhatsApp / TikTok 双平台。

## 环境准备

1. 安装依赖：`pip install -r requirements.txt`
2. 配置环境变量（或复制 `.env.example` 为 `.env`）：
  - `IM_API_BASE_URL`：接口基础地址，如 `https://host`，不带末尾斜杠
  - `IM_API_KEY`：管理员记录中的 API Key，请求头使用 `X-Api-Key`

所有接口入参时间均为**毫秒时间戳**。CLI 的 `--start/--end` 等参数同时接受纯数字时间戳或 `yyyy-MM-dd HH:mm` 字符串（按东八区解析）。

## 全局参数

- `--platform whatsapp|tiktok`（默认 `whatsapp`）：选择平台

## 查询前先确认可见平台账号（重要）

查询联系人、消息或其他平台数据前，先查询当前 API Key 可见的平台账号：

```bash
python im-agent-cli.py accounts
python im-agent-cli.py --platform tiktok accounts
```

如果 WhatsApp 账号列表为空，就跳过所有 WhatsApp 查询；如果 TikTok 账号列表为空，就跳过所有 TikTok 查询。跨平台任务只查询有可见账号的平台，并在结果中说明被跳过的平台，避免无效请求、节省时间。

## 先定位 ID（重要）

`messages` / `replies` / `efficiency` 的 `--csr` 以及 `messages` 的 `--contact` 需要的是**数字 ID**。先搜索定位：

```bash
python im-agent-cli.py csrs
python im-agent-cli.py contacts --keyword 138
```

## 子命令一览

| 命令 | 说明 |
|------|------|
| `ts` | 时间字符串转毫秒时间戳 |
| `accounts` | 平台账号列表 |
| `contacts` | 客户明细 / 搜索（支持 stageLevel、经销商和已下发过滤） |
| `contact` | 按 contactId 取客户详情 |
| `messages` | 消息明细（contactId 必传，无分页，支持 `--chat-only`） |
| `replies` | 回复明细 |
| `efficiency` | 回复时效聚合 |
| `distribution` | 客户检索条件分布 |
| `csrs` | 客服列表 |
| `stages` | 标签字典（含等级 stageLevel） |
| `dcc` | DCC 看板统计 |

## 用法示例

```bash
# 时间转换
python im-agent-cli.py ts "2026-06-01 00:00"

# 平台账号
python im-agent-cli.py accounts
python im-agent-cli.py --platform tiktok accounts

# 客服列表
python im-agent-cli.py csrs

# 标签字典
python im-agent-cli.py stages --lang cn

# 客户搜索（按标签等级 H 级 + 地区 CN）
python im-agent-cli.py contacts --stage-level H --area CN
python im-agent-cli.py contacts --keyword 13800000000
python im-agent-cli.py contacts --stage ice_breaking,deal --start "2026-01-01 00:00"
# 已下发线索：已绑定经销商，即 dealerId > 0
python im-agent-cli.py contacts --distributed
python im-agent-cli.py contacts --dealer-id 12

# 客户详情
python im-agent-cli.py contact 100023

# 消息明细（contactId 必传）
python im-agent-cli.py messages --contact 100023 --start "2026-06-01 00:00" --end "2026-06-16 23:59"

# 精简对话模式（仅方向+内容+客服+时间）
python im-agent-cli.py messages --contact 100023 --start "2026-06-01 00:00" --end "2026-06-16 23:59" --chat-only

# 回复明细
python im-agent-cli.py replies --start "2026-06-01 00:00" --end "2026-06-16 23:59" --csr 12 --mode ACCEPT,MODIFIED

# 回复时效
python im-agent-cli.py efficiency --start "2026-06-01 00:00" --end "2026-06-16 23:59"

# 客户分布
python im-agent-cli.py distribution --stage-level A --lang cn

# DCC 看板
python im-agent-cli.py dcc --start "2026-06-01 00:00" --end "2026-06-30 23:59"

# TikTok 平台
python im-agent-cli.py --platform tiktok contacts --keyword 张三
python im-agent-cli.py --platform tiktok messages --contact 200045 --start "2026-06-01 00:00" --end "2026-06-16 23:59"
```

## 工具函数（tools.py，可在脚本/AI 中直接调用）

- `parse_datetime("yyyy-MM-dd HH:mm") -> int`：转毫秒时间戳
- `format_millis(ms) -> str`：毫秒时间戳转可读字符串
- `query_accounts(platform)`：平台账号列表
- `query_contacts(platform, ...)`：客户搜索（支持 `stage_level`、`dealer_id`、`dealer_assigned`）
- `get_contact(contact_id, platform)`：客户详情
- `query_messages(contact_id, start_time, end_time, ..., chat_only)`：消息明细（contactId 必传，chatOnly 精简模式）
- `query_replies(...)`：回复明细
- `query_efficiency(...)`：回复时效聚合
- `query_distribution(...)`：客户分布
- `query_csrs()`：客服列表
- `query_stages(lang)`：标签字典
- `query_dcc_stats(start_time, end_time)`：DCC 看板

## 字段值含义

- `direction`：`inbound`=客户发来 / `outbound`=企业发出
- `csrId` / `repliedByCsrId`：`-1`=自动驾驶 / `0`=共享池 / `>0`=客服ID
- `assignedCsrId`：`0`=共享池 / `-1`=可抢占 / `>0`=已分配客服
- `dealerId`：经销商 ID，`0` 或空值=未下发，`>0`=已下发
- **口径**：下发指已绑定经销商（`dealerId > 0`）；分配指已分配客服（`assignedCsrId > 0`）。`assignedCsrId` 不用于判断是否下发。使用 `contacts --distributed` 过滤已下发线索。
- `linkAccounts`：`null`/`0`=未建联 / `>0`=已建联WA账号ID
- `acceptMode`：`ACCEPT`=无修改发送 / `MODIFIED`=修改后发送 / `MANUAL`=手动 / `REJECTED`=未发送
- `needReply`：`1`=待回复 / `0`=已回复 / `-1`=无需回复
- `stageLevel`：`H`/`A`/`B`/`C`/`D` 等级分类

## 指标计算提示

- **平均首次回复时长**：取 inbound 的 `waitSeconds` 求和 / 已回复单聊数
- **已回复单聊占比**：有 inbound 的客户中 `repliedAt` 非空的占比
- **回复形式分布**：用 `replies` 的 `acceptMode` 聚合

接口字段与参数详见 `API.md`。
