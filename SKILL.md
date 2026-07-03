---

## name: im-cli
description: 通过命令行查询 Carcolate-IM 开放接口（回复明细 / 消息时效 / 完整来往消息 / 客户明细 / 客服 / 外呼记录）。当需要按时间段、按客服、按客户、按标签拉取 IM 业务数据做统计分析或还原完整对话时使用。内置时间字符串转毫秒时间戳工具。

# im-cli

对接 Carcolate-IM OpenAPI 的 CLI 工具，三组数据：回复明细、消息明细（回复时效原始数据）、客户明细。

## 环境准备

1. 安装依赖：`pip install -r requirements.txt`
2. 配置环境变量（或复制 `.env.example` 为 `.env`）：
  - `IM_API_BASE_URL`：接口基础地址，如 `https://host`，不带末尾斜杠
  - `IM_API_KEY`：来自 `tb_openapi_key.api_key`，请求头 `X-Api-Key` 使用

所有接口入参时间均为**毫秒时间戳**。CLI 的 `--start/--end` 等参数同时接受纯数字时间戳或 `yyyy-MM-dd HH:mm` 字符串（按东八区解析）。

## 先定位 ID（重要）

`replies` / `messages` 的 `--csr` / `--contact` 需要的是**数字 ID**，不是名字。AI/调用方一般只知道
客服名或客户名/手机号，所以先用 `csrs` / `contacts` 按关键词搜出 id，再带入其它命令：

```bash
# 按名字搜客服 -> 拿到 id
python im-agent-cli.py csrs --keyword 张三
# 按手机号/昵称搜客户 -> 拿到 id
python im-agent-cli.py contacts --keyword 138
```

## 用法

```bash
# 时间字符串 -> 毫秒时间戳
python im-agent-cli.py ts "2026-06-01 00:00"

# 客服：搜索 / 按 id 取详情
python im-agent-cli.py csrs --keyword 张三
python im-agent-cli.py csr 12

# 客户：搜索 / 按 id 取详情
python im-agent-cli.py contacts --keyword 13800000000
python im-agent-cli.py contact 100023 --lang cn

# 回复明细（必填起止时间）
python im-agent-cli.py replies --start "2026-06-01 00:00" --end "2026-06-16 23:59" --csr 12 --mode ACCEPT,MODIFIED
python im-agent-cli.py replies --start "2026-06-01 00:00" --end "2026-06-16 23:59" --keyword 价格

# 消息明细（回复时效原始数据），只看某客户已回复的 inbound
python im-agent-cli.py messages --start "2026-06-01 00:00" --end "2026-06-16 23:59" --direction inbound --has-reply true

# 完整来往消息（inbound+outbound 对话流），取单个客户的完整对话
python im-agent-cli.py conversations --start "2026-06-01 00:00" --end "2026-06-16 23:59" --contact 100023

# 标签变更流水（某客户 stage 的历次变化）
python im-agent-cli.py stage-logs --contact 100023 --start "2026-06-01 00:00" --end "2026-06-16 23:59"

# 客户明细：按标签 + 地区 + 初次联系时间过滤
python im-agent-cli.py contacts --stage ice_breaking,deal --area CN --start "2026-01-01 00:00" --lang cn

# 客户明细：扩展过滤（id/昵称/总结关键字/lastSeen 区间/WA 账号）
python im-agent-cli.py contacts --id 100023
python im-agent-cli.py contacts --nick 张 --summary 价格 --last-seen-start "2026-06-01 00:00" --last-seen-end "2026-06-16 23:59" --link-accounts 3

# 客户检索条件分布（stage / csr / area / needReply 四段聚合，不分页）
python im-agent-cli.py distribution --stage ice_breaking,deal_closed --area CN --start "2026-01-01 00:00" --lang cn

# 外呼记录（客服在「外呼」Tab 拨打线索的明细，按时间/客服/客户/通话结果过滤）
python im-agent-cli.py call-logs --start "2026-06-01 00:00" --end "2026-06-16 23:59" --outcome connected
python im-agent-cli.py call-logs --csr 12 --outcome no_answer
```

## 工具函数（tools.py，可在脚本/AI 中直接调用）

- `parse_datetime("yyyy-MM-dd HH:mm") -> int`：转毫秒时间戳
- `format_millis(ms) -> str`：毫秒时间戳转可读字符串
- `query_csrs(...)` / `get_csr(id)`：搜索客服 / 取客服详情（定位 csrId）
- `query_contacts(...)` / `get_contact(id)`：搜索客户 / 取客户详情（定位 contactId）。
  扩展入参：`link_accounts`、`contact_id`(精确ID)、`nick_name`(模糊昵称)、`summary_keyword`、`last_seen_start/end`
- `query_contact_distribution(...)`：按 contacts 同名筛选条件聚合，输出 `{total, stage[], csr[], area[], needReply[]}`，不分页
- `query_replies(...)` / `query_messages(...)`：回复明细 / 消息时效原始数据。`query_replies` 支持 `keyword`（模糊匹配 textContent / copilotSuggestion）
- `query_conversations(...)`：完整来往消息（inbound+outbound 对话流，含正文/媒体/copilot 痕迹）
- `query_stage_logs(...)`：客户标签(stage)变更流水（stageFrom/stageTo 为标签数组，带客户昵称）
- `query_call_logs(...)`：外呼记录（客服拨打线索明细，含 `outcome`/`remark`/`callAt`），用于接通率/外呼工作量等分析

## 字段值含义（纯值字段说明）

涉及消息 / 客户 / 回复的接口里，有些字段是纯枚举值，含义如下，统计时务必区分：

- `direction`（消息方向）：
  - `inbound`=客户发来的消息
  - `outbound`=企业/客服发出的消息
  - `autoback`=**系统按 WhatsApp 状态回调补建的兜底数据，不代表"自动发送"**。历史脏数据已批量修正，新数据基本不再产生；统计发送量时一般并入 outbound 看待。
- `csrId` / `repliedByCsrId`（归属/回复客服）：
  - `-1`=**自动驾驶(autopilot)后台自动发送，无客服干预**
  - `0`=共享池（所有人可见、可回复）
  - `>0`=具体客服 ID
  - `null`=暂无归属
- `assignedCsrId`（客户分配客服）：
  - `0`=共享池
  - `-1`=可抢占但尚未被领取
  - `>0`=已分配给该客服
- `linkAccounts`（客户来源 WA 账号）：
  - `null` / `0`=**未建联线索**（导入未发模板 / 等客户主动联系），在客服端「外呼」Tab 展示，靠电话触达
  - `>0`=对应 `tb_wa_accounts.id`，已建联，在「对话」Tab 展示
  - 客户主动来 WhatsApp 消息后会自动从 0 升级为对应 wa_account.id，调用方无需感知
- `outcome`（外呼记录通话结果）：
  - `connected`=已接通 / `no_answer`=无人接听 / `rejected`=拒接 / `wrong_number`=错号 / `invalid`=空号停机
  - `null`=客服仅记录了「拨号动作」，未回填结果
- `acceptMode`（copilot 回复形式）：
  - `ACCEPT`=无修改直接发送
  - `MODIFIED`=在建议基础上修改后发送
  - `MANUAL`=客服手动编写（非基于 copilot 建议）
  - `REJECTED`=拒绝该建议，未发送
- `needReply`（待回复状态）：`1`=待回复 / `0`=已回复 / `-1`=无需回复。

## 指标计算提示

`/openapi/messages` 返回原始消息行，不做聚合。调用方可自行计算：

- **平均首次回复时长**：取一天内每个客户首条 inbound（`repliedAt` 非空）的 `waitSeconds`，求和 / 已回复单聊数。
- **已回复单聊占比**：当天有 inbound 的客户中，被回复（`repliedAt` 非空）的客户占比。
- **回复形式分布**：用 `/openapi/replies` 的 `acceptMode`（ACCEPT=无修改 / MODIFIED=修改后 / MANUAL=手动 / REJECTED=未发送）聚合。

接口字段与参数详见 `API.md`。