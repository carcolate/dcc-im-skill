#!/usr/bin/env python3
"""im-cli：对接 Carcolate-IM OpenAPI 的命令行工具。

子命令：
  ts        把 'yyyy-MM-dd HH:mm' 转成毫秒时间戳
  replies   查询回复明细
  messages  查询消息明细（回复时效原始数据）
  contacts  查询客户明细

时间参数同时支持毫秒时间戳（纯数字）和 'yyyy-MM-dd HH:mm' 字符串。
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from api_client import ApiClient, ApiError
import tools


def _ts(value):
    """参数值 -> 毫秒时间戳：纯数字按时间戳，否则按 yyyy-MM-dd HH:mm 解析。"""
    if value is None:
        return None
    s = str(value).strip()
    if s.isdigit():
        return int(s)
    return tools.parse_datetime(s)


def _print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_ts(args):
    _print({"input": args.datetime, "millis": tools.parse_datetime(args.datetime)})


def cmd_replies(args):
    client = ApiClient()
    res = tools.query_replies(
        client, start_time=_ts(args.start), end_time=_ts(args.end),
        csr_id=args.csr, accept_mode=args.mode, contact_id=args.contact,
        page=args.page, size=args.size,
    )
    _print(res)


def cmd_messages(args):
    client = ApiClient()
    has_reply = None
    if args.has_reply is not None:
        has_reply = args.has_reply.lower() in ("1", "true", "yes", "y")
    res = tools.query_messages(
        client, start_time=_ts(args.start), end_time=_ts(args.end),
        csr_id=args.csr, contact_id=args.contact, direction=args.direction,
        has_reply=has_reply, page=args.page, size=args.size,
    )
    _print(res)


def cmd_contacts(args):
    client = ApiClient()
    res = tools.query_contacts(
        client, csr_id=args.csr, keyword=args.keyword, stage=args.stage, user_area=args.area,
        start_time=_ts(args.start), end_time=_ts(args.end),
        last_seen_after=_ts(args.last_seen_after), lang=args.lang,
        page=args.page, size=args.size,
    )
    _print(res)


def cmd_contact(args):
    client = ApiClient()
    _print(tools.get_contact(client, contact_id=args.id, lang=args.lang))


def cmd_csrs(args):
    client = ApiClient()
    _print(tools.query_csrs(client, keyword=args.keyword, status=args.status,
                            page=args.page, size=args.size))


def cmd_csr(args):
    client = ApiClient()
    _print(tools.get_csr(client, csr_id=args.id))


def build_parser():
    p = argparse.ArgumentParser(description="Carcolate-IM OpenAPI 命令行工具")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("ts", help="时间字符串转毫秒时间戳")
    sp.add_argument("datetime", help="yyyy-MM-dd HH:mm")
    sp.set_defaults(func=cmd_ts)

    sp = sub.add_parser("replies", help="回复明细")
    sp.add_argument("--start", required=True, help="起始时间（时间戳或 yyyy-MM-dd HH:mm）")
    sp.add_argument("--end", required=True, help="结束时间（时间戳或 yyyy-MM-dd HH:mm）")
    sp.add_argument("--csr", type=int, help="回复人 csrId")
    sp.add_argument("--mode", help="copilot_accept_mode 逗号分隔，如 ACCEPT,MODIFIED")
    sp.add_argument("--contact", type=int, help="客户ID")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=50)
    sp.set_defaults(func=cmd_replies)

    sp = sub.add_parser("messages", help="消息明细（回复时效原始数据）")
    sp.add_argument("--start", required=True, help="起始时间（时间戳或 yyyy-MM-dd HH:mm）")
    sp.add_argument("--end", required=True, help="结束时间（时间戳或 yyyy-MM-dd HH:mm）")
    sp.add_argument("--csr", type=int, help="客服 csrId")
    sp.add_argument("--contact", type=int, help="客户ID")
    sp.add_argument("--direction", help="inbound / outbound")
    sp.add_argument("--has-reply", dest="has_reply", help="true/false：仅 inbound 已回复/未回复")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=50)
    sp.set_defaults(func=cmd_messages)

    sp = sub.add_parser("contacts", help="客户明细 / 搜索")
    sp.add_argument("--csr", type=int, help="分配客服 csrId")
    sp.add_argument("--keyword", help="模糊匹配 昵称/备注/手机号")
    sp.add_argument("--stage", help="stage_key 逗号分隔")
    sp.add_argument("--area", help="国家地区代码，如 CN")
    sp.add_argument("--start", help="firstSeen >= （时间戳或 yyyy-MM-dd HH:mm）")
    sp.add_argument("--end", help="firstSeen <= （时间戳或 yyyy-MM-dd HH:mm）")
    sp.add_argument("--last-seen-after", dest="last_seen_after", help="lastSeen >= （时间戳或 yyyy-MM-dd HH:mm）")
    sp.add_argument("--lang", default="cn", help="cn / en，影响 stageNames")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=50)
    sp.set_defaults(func=cmd_contacts)

    sp = sub.add_parser("contact", help="按 contactId 取客户详情")
    sp.add_argument("id", type=int, help="客户ID")
    sp.add_argument("--lang", default="cn", help="cn / en，影响 stageNames")
    sp.set_defaults(func=cmd_contact)

    sp = sub.add_parser("csrs", help="客服列表 / 搜索（定位 csrId）")
    sp.add_argument("--keyword", help="模糊匹配 name/account/phone/email")
    sp.add_argument("--status", type=int, help="0=禁用 1=启用")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=50)
    sp.set_defaults(func=cmd_csrs)

    sp = sub.add_parser("csr", help="按 csrId 取客服信息")
    sp.add_argument("id", type=int, help="客服ID")
    sp.set_defaults(func=cmd_csr)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (ApiError, ValueError) as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
