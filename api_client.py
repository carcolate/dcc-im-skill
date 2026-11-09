"""OpenAPI 请求封装：统一注入 X-Api-Key，处理基础地址与错误。"""
from __future__ import annotations

import os
import re
from typing import Any, Callable, Dict, Optional

import requests


class ApiError(Exception):
    def __init__(self, message: str, *, code: Optional[int] = None,
                 payload: Any = None, cancelled: bool = False):
        super().__init__(message)
        self.code = code
        self.payload = payload
        self.cancelled = cancelled


class ApiClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None,
                 timeout: int = 30, confirm: Optional[Callable[[str], bool]] = None):
        self.base_url = (base_url or os.getenv("IM_API_BASE_URL") or "").rstrip("/")
        self.api_key = api_key or os.getenv("IM_API_KEY") or ""
        self.timeout = timeout
        self.confirm = confirm
        if not self.base_url:
            raise ApiError("缺少 IM_API_BASE_URL（环境变量或 .env）")
        if not self.api_key:
            raise ApiError("缺少 IM_API_KEY（环境变量或 .env）")

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self.base_url + path
        headers = {"X-Api-Key": self.api_key, "Accept": "application/json"}
        retried = False
        questions = set()
        while True:
            try:
                resp = requests.get(url, params=params or {}, headers=headers, timeout=self.timeout)
            except requests.RequestException as e:
                raise ApiError(f"请求失败：{e}") from e

            if resp.status_code != 200:
                raise ApiError(f"HTTP {resp.status_code}: {resp.text[:500]}")

            try:
                data = resp.json()
            except ValueError as e:
                raise ApiError(f"返回非 JSON：{resp.text[:500]}") from e

            # 保留原始响应结构，供分页和现有工具函数使用。
            if not isinstance(data, dict) or data.get("code") in (0, None):
                return data
            code = data.get("code")
            message = data.get("msg") or data.get("msgEn") or "请求失败"
            if code == 1 and not retried:
                retried = True
                continue
            if code == 22:
                raw_question = data.get("tryQues")
                question = "" if raw_question is None else str(raw_question)
                if (question and not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", question)) or question in questions or len(questions) >= 3:
                    raise ApiError("确认重试无效或超过次数限制", code=code, payload=data)
                if self.confirm is None:
                    raise ApiError(f"需要人工确认，未执行重试：{message}", code=code, payload=data)
                if not self.confirm(message):
                    raise ApiError("已取消确认，未执行重试", code=code, payload=data, cancelled=True)
                questions.add(question)
                headers[f"confirm-{question}" if question else "confirm"] = "ok"
                continue
            if code == 20:
                raise ApiError("请求已中断（code=20）", code=code, payload=data)
            raise ApiError(str(message), code=code, payload=data)
