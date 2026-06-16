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


def query_contacts(client: ApiClient, csr_id: Optional[int] = None, stage: Optional[str] = None,
                   user_area: Optional[str] = None, start_time: Optional[int] = None,
                   end_time: Optional[int] = None, last_seen_after: Optional[int] = None,
                   lang: str = "cn", page: int = 1, size: int = 50):
    """客户明细。时间参数为毫秒时间戳（均选填）。"""
    params = {"lang": lang, "page": page, "size": size}
    if csr_id is not None:
        params["csrId"] = csr_id
    if stage:
        params["stage"] = stage
    if user_area:
        params["userArea"] = user_area
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time
    if last_seen_after is not None:
        params["lastSeenAfter"] = last_seen_after
    return client.get("/openapi/contacts", params)
