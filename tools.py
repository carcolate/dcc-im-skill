"""工具函数：时间戳转换 + 三组开放接口查询封装。

设计给 AI / 脚本调用：所有时间参数对外暴露为毫秒时间戳，
parse_datetime 负责把人类可读的 'yyyy-MM-dd HH:mm' 转成毫秒。
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from api_client import ApiClient

# 默认时区：东八区（与后端 serverTimezone=GMT+8 对齐）
DEFAULT_TZ = timezone(timedelta(hours=8))


def parse_datetime(s: str, tz_offset_hours: int = 8) -> int:
    """把 'yyyy-MM-dd HH:mm' 或 'yyyy-MM-dd HH:mm:ss' 转成毫秒时间戳。

    也兼容只给日期 'yyyy-MM-dd'（按当天 00:00 处理）。
    tz_offset_hours：输入时间所在时区相对 UTC 的小时偏移，默认东八区。
    """
    s = (s or "").strip()
    fmts = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
    last_err: Optional[Exception] = None
    tz = timezone(timedelta(hours=tz_offset_hours))
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt).replace(tzinfo=tz)
            return int(dt.timestamp() * 1000)
        except ValueError as e:
            last_err = e
    raise ValueError(f"无法解析时间 '{s}'，请用 yyyy-MM-dd HH:mm 格式。原始错误：{last_err}")


def format_millis(ms: Optional[int], tz_offset_hours: int = 8) -> str:
    """毫秒时间戳 -> 'yyyy-MM-dd HH:mm:ss'，便于阅读。None 返回 '-'。"""
    if ms is None:
        return "-"
    tz = timezone(timedelta(hours=tz_offset_hours))
    return datetime.fromtimestamp(ms / 1000, tz).strftime("%Y-%m-%d %H:%M:%S")


def query_replies(client: ApiClient, start_time: int, end_time: int,
                  csr_id: Optional[int] = None, accept_mode: Optional[str] = None,
                  contact_id: Optional[int] = None, page: int = 1, size: int = 50):
    """回复明细。start_time/end_time 为毫秒时间戳（必填）。"""
    params = {"startTime": start_time, "endTime": end_time, "page": page, "size": size}
    if csr_id is not None:
        params["csrId"] = csr_id
    if accept_mode:
        params["acceptMode"] = accept_mode
    if contact_id is not None:
        params["contactId"] = contact_id
    return client.get("/openapi/replies", params)


def query_messages(client: ApiClient, start_time: int, end_time: int,
                   csr_id: Optional[int] = None, contact_id: Optional[int] = None,
                   direction: Optional[str] = None, has_reply: Optional[bool] = None,
                   page: int = 1, size: int = 50):
    """消息明细（回复时效原始数据）。start_time/end_time 为毫秒时间戳（必填）。"""
    params = {"startTime": start_time, "endTime": end_time, "page": page, "size": size}
    if csr_id is not None:
        params["csrId"] = csr_id
    if contact_id is not None:
        params["contactId"] = contact_id
    if direction:
        params["direction"] = direction
    if has_reply is not None:
        params["hasReply"] = "true" if has_reply else "false"
    return client.get("/openapi/messages", params)


def query_conversations(client: ApiClient, start_time: int, end_time: int,
                        contact_id: Optional[int] = None, csr_id: Optional[int] = None,
                        direction: Optional[str] = None, page: int = 1, size: int = 200):
    """完整来往消息：按时间段拉取 inbound+outbound 完整对话流（含正文/媒体/copilot 痕迹），
    按客户分组、时间升序。start_time/end_time 为毫秒时间戳（必填）。"""
    params = {"startTime": start_time, "endTime": end_time, "page": page, "size": size}
    if contact_id is not None:
        params["contactId"] = contact_id
    if csr_id is not None:
        params["csrId"] = csr_id
    if direction:
        params["direction"] = direction
    return client.get("/openapi/conversations", params)


def query_stage_logs(client: ApiClient, contact_id: Optional[int] = None,
                     start_time: Optional[int] = None, end_time: Optional[int] = None,
                     page: int = 1, size: int = 50):
    """客户标签(stage)变更流水。带客户昵称；stageFrom/stageTo 为标签数组。时间为毫秒时间戳（均选填）。"""
    params = {"page": page, "size": size}
    if contact_id is not None:
        params["contactId"] = contact_id
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time
    return client.get("/openapi/stage-logs", params)


def query_contacts(client: ApiClient, csr_id: Optional[int] = None, keyword: Optional[str] = None,
                   stage: Optional[str] = None, user_area: Optional[str] = None,
                   start_time: Optional[int] = None, end_time: Optional[int] = None,
                   last_seen_start: Optional[int] = None, last_seen_end: Optional[int] = None,
                   last_seen_after: Optional[int] = None,
                   link_accounts: Optional[int] = None, contact_id: Optional[int] = None,
                   nick_name: Optional[str] = None, summary_keyword: Optional[str] = None,
                   lang: str = "cn", page: int = 1, size: int = 50):
    """客户明细 / 搜索。keyword 模糊匹配昵称/备注/手机号。时间参数为毫秒时间戳（均选填）。
    扩展参数：link_accounts(WA账号), contact_id(精确ID), nick_name(模糊昵称),
    summary_keyword(会话总结关键字), last_seen_start/end(最后互动时间区间)。"""
    params = {"lang": lang, "page": page, "size": size}
    if csr_id is not None:
        params["csrId"] = csr_id
    if keyword:
        params["keyword"] = keyword
    if stage:
        params["stage"] = stage
    if user_area:
        params["userArea"] = user_area
    if link_accounts is not None:
        params["linkAccounts"] = link_accounts
    if contact_id is not None:
        params["id"] = contact_id
    if nick_name:
        params["nickName"] = nick_name
    if summary_keyword:
        params["summaryKeyword"] = summary_keyword
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time
    if last_seen_start is not None:
        params["lastSeenStart"] = last_seen_start
    if last_seen_end is not None:
        params["lastSeenEnd"] = last_seen_end
    if last_seen_after is not None:
        params["lastSeenAfter"] = last_seen_after
    return client.get("/openapi/contacts", params)


def query_contact_distribution(client: ApiClient, csr_id: Optional[int] = None, keyword: Optional[str] = None,
                               stage: Optional[str] = None, user_area: Optional[str] = None,
                               start_time: Optional[int] = None, end_time: Optional[int] = None,
                               last_seen_start: Optional[int] = None, last_seen_end: Optional[int] = None,
                               last_seen_after: Optional[int] = None,
                               link_accounts: Optional[int] = None, contact_id: Optional[int] = None,
                               nick_name: Optional[str] = None, summary_keyword: Optional[str] = None,
                               lang: str = "cn"):
    """客户检索条件分布：对当前筛选命中的客户集合输出 stage/csr/area/needReply 四种饼图源数据。
    入参与 query_contacts 相同（不接受 page/size），返回 {total, stage[], csr[], area[], needReply[]}。"""
    params = {"lang": lang}
    if csr_id is not None:
        params["csrId"] = csr_id
    if keyword:
        params["keyword"] = keyword
    if stage:
        params["stage"] = stage
    if user_area:
        params["userArea"] = user_area
    if link_accounts is not None:
        params["linkAccounts"] = link_accounts
    if contact_id is not None:
        params["id"] = contact_id
    if nick_name:
        params["nickName"] = nick_name
    if summary_keyword:
        params["summaryKeyword"] = summary_keyword
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time
    if last_seen_start is not None:
        params["lastSeenStart"] = last_seen_start
    if last_seen_end is not None:
        params["lastSeenEnd"] = last_seen_end
    if last_seen_after is not None:
        params["lastSeenAfter"] = last_seen_after
    return client.get("/openapi/contacts/distribution", params)


def get_contact(client: ApiClient, contact_id: int, lang: str = "cn"):
    """按 contactId 取单个客户详情。"""
    return client.get(f"/openapi/contacts/{contact_id}", {"lang": lang})


def query_csrs(client: ApiClient, keyword: Optional[str] = None, status: Optional[int] = None,
               page: int = 1, size: int = 50):
    """客服列表 / 搜索。keyword 模糊匹配 name/account/phone/email，用于定位 csrId。"""
    params = {"page": page, "size": size}
    if keyword:
        params["keyword"] = keyword
    if status is not None:
        params["status"] = status
    return client.get("/openapi/csrs", params)


def get_csr(client: ApiClient, csr_id: int):
    """按 csrId 取单个客服信息（已脱敏）。"""
    return client.get(f"/openapi/csrs/{csr_id}", {})


def query_call_logs(client: ApiClient, contact_id: Optional[int] = None,
                    csr_id: Optional[int] = None, outcome: Optional[str] = None,
                    start_time: Optional[int] = None, end_time: Optional[int] = None,
                    page: int = 1, size: int = 50):
    """外呼记录：客服在「外呼」Tab 拨打线索的明细。按 callAt 倒序。
    outcome 取值：connected/no_answer/rejected/wrong_number/invalid。
    时间为毫秒时间戳，均选填。"""
    params = {"page": page, "size": size}
    if contact_id is not None:
        params["contactId"] = contact_id
    if csr_id is not None:
        params["csrId"] = csr_id
    if outcome:
        params["outcome"] = outcome
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time
    return client.get("/openapi/call-logs", params)
