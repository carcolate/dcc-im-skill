---
name: im-cli
description: 通过命令行查询 Carcolate-IM 开放接口（回复明细 / 消息时效 / 完整来往消息 / 客户明细 / 客服）。当需要按时间段、按客服、按客户、按标签拉取 IM 业务数据做统计分析或还原完整对话时使用。内置时间字符串转毫秒时间戳工具。
---

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

# 消息明细（回复时效原始数据），只看某客户已回复的 inbound
python im-agent-cli.py messages --start "2026-06-01 00:00" --end "2026-06-16 23:59" --direction inbound --has-reply true

# 完整来往消息（inbound+outbound 对话流），取单个客户的完整对话
python im-agent-cli.py conversations --start "2026-06-01 00:00" --end "2026-06-16 23:59" --contact 100023

# 客户明细，按标签 + 地区 + 初次联系时间过滤
python im-agent-cli.py contacts --stage ice_breaking,deal --area CN --start "2026-01-01 00:00" --lang cn
```

## 工具函数（tools.py，可在脚本/AI 中直接调用）

- `parse_datetime("yyyy-MM-dd HH:mm") -> int`：转毫秒时间戳
- `format_millis(ms) -> str`：毫秒时间戳转可读字符串
- `query_csrs(...)` / `get_csr(id)`：搜索客服 / 取客服详情（定位 csrId）
- `query_contacts(...)` / `get_contact(id)`：搜索客户 / 取客户详情（定位 contactId，`query_contacts` 支持 `keyword`）
- `query_replies(...)` / `query_messages(...)`：回复明细 / 消息时效原始数据
- `query_conversations(...)`：完整来往消息（inbound+outbound 对话流，含正文/媒体/copilot 痕迹）

## 指标计算提示

`/openapi/messages` 返回原始消息行，不做聚合。调用方可自行计算：

- **平均首次回复时长**：取一天内每个客户首条 inbound（`repliedAt` 非空）的 `waitSeconds`，求和 / 已回复单聊数。
- **已回复单聊占比**：当天有 inbound 的客户中，被回复（`repliedAt` 非空）的客户占比。
- **回复形式分布**：用 `/openapi/replies` 的 `acceptMode`（ACCEPT=无修改 / MODIFIED=修改后 / MANUAL=手动 / REJECTED=未发送）聚合。

接口字段与参数详见 `API.md`。
