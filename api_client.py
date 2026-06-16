"""OpenAPI 请求封装：统一注入 X-Api-Key，处理基础地址与错误。"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None,
                 timeout: int = 30):
        self.base_url = (base_url or os.getenv("IM_API_BASE_URL") or "").rstrip("/")
        self.api_key = api_key or os.getenv("IM_API_KEY") or ""
        self.timeout = timeout
        if not self.base_url:
            raise ApiError("缺少 IM_API_BASE_URL（环境变量或 .env）")
        if not self.api_key:
            raise ApiError("缺少 IM_API_KEY（环境变量或 .env）")

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self.base_url + path
        headers = {"X-Api-Key": self.api_key, "Accept": "application/json"}
        try:
            resp = requests.get(url, params=params or {}, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise ApiError(f"请求失败：{e}")

        if resp.status_code != 200:
            raise ApiError(f"HTTP {resp.status_code}: {resp.text[:500]}")

        try:
            data = resp.json()
        except ValueError:
            raise ApiError(f"返回非 JSON：{resp.text[:500]}")

        # 后端统一 Rsp 结构：code==0 成功
        if isinstance(data, dict) and data.get("code") not in (0, None):
            raise ApiError(f"接口错误 code={data.get('code')} msg={data.get('msg')}")
        return data
