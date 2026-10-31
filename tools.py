"""工具函数：时间戳转换 + V2 OpenAPI 查询封装。

所有时间参数对外暴露为毫秒时间戳，parse_datetime 负责把人类可读的 'yyyy-MM-dd HH:mm' 转成毫秒。
接口路径统一走 /openapi/v2/，platform 参数决定 whatsapp / tiktok 子路径。
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from api_client import ApiClient

DEFAULT_TZ = timezone(timedelta(hours=8))


def parse_datetime(s: str, tz_offset_hours: int = 8) -> int:
    """把 'yyyy-MM-dd HH:mm' 或 'yyyy-MM-dd HH:mm:ss' 转成毫秒时间戳。
    也兼容只给日期 'yyyy-MM-dd'（按当天 00:00 处理）。"""
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


# ── V2 平台接口 ──

def _platform_path(platform: str) -> str:
    return f"/openapi/v2/{platform}"


def query_accounts(client: ApiClient, platform: str = "whatsapp"):
    """平台账号列表。"""
    response = client.get(f"{_platform_path(platform)}/accounts")
    data = response.get("data") if isinstance(response, dict) else None
    rows = data if isinstance(data, list) else []
    if isinstance(data, dict):
        rows = data.get("records") or data.get("list") or data.get("rows") or []
    for row in rows:
        if isinstance(row, dict):
            row.pop("provider", None)
    return response


def query_contacts(client: ApiClient, platform: str = "whatsapp",
                   csr_id: Optional[int] = None, keyword: Optional[str] = None,
                   stage: Optional[str] = None, stage_level: Optional[str] = None,
                   user_area: Optional[str] = None,
                   start_time: Optional[int] = None, end_time: Optional[int] = None,
                   last_seen_start: Optional[int] = None, last_seen_end: Optional[int] = None,
                   link_accounts: Optional[int] = None,
                   platform_account_id: Optional[int] = None,
                   contact_id: Optional[int] = None,
                   nick_name: Optional[str] = None, summary_keyword: Optional[str] = None,
                   lang: str = "cn", page: int = 1, size: int = 50,
                   dealer_id: Optional[int] = None,
                   dealer_assigned: Optional[bool] = None):
    """客户明细 / 搜索。"""
    params = {"lang": lang, "page": page, "size": size}
    if csr_id is not None:
        params["csrId"] = csr_id
    if dealer_id is not None:
        params["dealerId"] = dealer_id
    if dealer_assigned is not None:
        params["dealerAssigned"] = "true" if dealer_assigned else "false"
    if keyword:
        params["keyword"] = keyword
    if stage:
        params["stage"] = stage
    if stage_level:
        params["stageLevel"] = stage_level
    if user_area:
        params["userArea"] = user_area
    if link_accounts is not None:
        params["linkAccounts"] = link_accounts
    if platform_account_id is not None:
        params["platformAccountId"] = platform_account_id
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
    return client.get(f"{_platform_path(platform)}/contacts", params)


def get_contact(client: ApiClient, contact_id: int, platform: str = "whatsapp",
                lang: str = "cn"):
    """按 contactId 取单个客户详情。"""
    return client.get(f"{_platform_path(platform)}/contacts/{contact_id}", {"lang": lang})


def query_messages(client: ApiClient, contact_id: int,
                   start_time: int, end_time: int,
                   platform: str = "whatsapp",
                   csr_id: Optional[int] = None,
                   direction: Optional[str] = None,
                   has_reply: Optional[bool] = None,
                   chat_only: bool = False):
    """消息明细。contactId 必传，不分页。chatOnly=True 只返回精简对话字段。"""
    params = {"contactId": contact_id, "startTime": start_time, "endTime": end_time}
    if csr_id is not None:
        params["csrId"] = csr_id
    if direction:
        params["direction"] = direction
    if has_reply is not None:
        params["hasReply"] = "true" if has_reply else "false"
    if chat_only:
        params["chatOnly"] = "true"
    return client.get(f"{_platform_path(platform)}/messages", params)


def query_replies(client: ApiClient, start_time: int, end_time: int,
                  platform: str = "whatsapp",
                  csr_id: Optional[int] = None, contact_id: Optional[int] = None,
                  accept_mode: Optional[str] = None,
                  keyword: Optional[str] = None,
                  page: int = 1, size: int = 50):
    """回复明细。"""
    params = {"startTime": start_time, "endTime": end_time, "page": page, "size": size}
    if csr_id is not None:
        params["csrId"] = csr_id
    if contact_id is not None:
        params["contactId"] = contact_id
    if accept_mode:
        params["acceptMode"] = accept_mode
    if keyword:
        params["keyword"] = keyword
    return client.get(f"{_platform_path(platform)}/replies", params)


def query_efficiency(client: ApiClient, start_time: int, end_time: int,
                     platform: str = "whatsapp",
                     csr_id: Optional[int] = None,
                     page: int = 1, size: int = 50):
    """回复时效聚合。"""
    params = {"startTime": start_time, "endTime": end_time, "page": page, "size": size}
    if csr_id is not None:
        params["csrId"] = csr_id
    return client.get(f"{_platform_path(platform)}/efficiency", params)


def query_distribution(client: ApiClient, platform: str = "whatsapp",
                       csr_id: Optional[int] = None,
                       stage: Optional[str] = None, stage_level: Optional[str] = None,
                       platform_account_id: Optional[int] = None,
                       lang: str = "cn"):
    """客户检索条件分布。"""
    params = {"lang": lang}
    if csr_id is not None:
        params["csrId"] = csr_id
    if stage:
        params["stage"] = stage
    if stage_level:
        params["stageLevel"] = stage_level
    if platform_account_id is not None:
        params["platformAccountId"] = platform_account_id
    return client.get(f"{_platform_path(platform)}/distribution", params)


# ── V2 通用接口 ──

def query_csrs(client: ApiClient):
    """客服列表（V2 通用接口）。"""
    return client.get("/openapi/v2/common/csrs")


def query_stages(client: ApiClient, lang: str = "cn"):
    """标签字典（V2 通用接口）。"""
    return client.get("/openapi/v2/common/stages", {"lang": lang})


def query_dcc_stats(client: ApiClient, start_time: int, end_time: int):
    """DCC 看板统计（V2 通用接口）。"""
    return client.get("/openapi/v2/common/dcc/stats",
                      {"startTime": start_time, "endTime": end_time})
