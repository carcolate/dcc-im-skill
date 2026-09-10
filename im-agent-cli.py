#!/usr/bin/env python3
"""im-cli：对接 Carcolate-IM V2 OpenAPI 的命令行工具。

子命令：
  ts            时间字符串转毫秒时间戳
  accounts      平台账号列表
  contacts      客户明细 / 搜索
  contact       按 contactId 取客户详情
  messages      消息明细（contactId 必传，无分页，支持 chatOnly 精简模式）
  replies       回复明细
  efficiency    回复时效聚合
  distribution  客户检索条件分布
  csrs          客服列表
  stages        标签字典
  dcc           DCC 看板统计

时间参数同时支持毫秒时间戳（纯数字）和 'yyyy-MM-dd HH:mm' 字符串。
全局参数 --platform 可选 whatsapp（默认） / tiktok。
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


def cmd_accounts(args):
    _print(tools.query_accounts(ApiClient(), platform=args.platform))


def cmd_contacts(args):
    _print(tools.query_contacts(
        ApiClient(), platform=args.platform,
        csr_id=args.csr, keyword=args.keyword,
        stage=args.stage, stage_level=args.stage_level,
        user_area=args.area,
        start_time=_ts(args.start), end_time=_ts(args.end),
        last_seen_start=_ts(args.last_seen_start), last_seen_end=_ts(args.last_seen_end),
        link_accounts=args.link_accounts,
        platform_account_id=args.platform_account_id,
        contact_id=args.id, nick_name=args.nick, summary_keyword=args.summary,
        lang=args.lang, page=args.page, size=args.size,
    ))


def cmd_contact(args):
    _print(tools.get_contact(ApiClient(), contact_id=args.id,
                             platform=args.platform, lang=args.lang))


def cmd_messages(args):
    has_reply = None
    if args.has_reply is not None:
        has_reply = args.has_reply.lower() in ("1", "true", "yes", "y")
    _print(tools.query_messages(
        ApiClient(), contact_id=args.contact,
        start_time=_ts(args.start), end_time=_ts(args.end),
        platform=args.platform, csr_id=args.csr,
        direction=args.direction, has_reply=has_reply,
        chat_only=args.chat_only,
    ))


def cmd_replies(args):
    _print(tools.query_replies(
        ApiClient(), start_time=_ts(args.start), end_time=_ts(args.end),
        platform=args.platform, csr_id=args.csr, contact_id=args.contact,
        accept_mode=args.mode, keyword=args.keyword,
        page=args.page, size=args.size,
    ))


def cmd_efficiency(args):
    _print(tools.query_efficiency(
        ApiClient(), start_time=_ts(args.start), end_time=_ts(args.end),
        platform=args.platform, csr_id=args.csr,
        page=args.page, size=args.size,
    ))


def cmd_distribution(args):
    _print(tools.query_distribution(
        ApiClient(), platform=args.platform,
        csr_id=args.csr, stage=args.stage, stage_level=args.stage_level,
        platform_account_id=args.platform_account_id, lang=args.lang,
    ))


def cmd_csrs(args):
    _print(tools.query_csrs(ApiClient()))


def cmd_stages(args):
    _print(tools.query_stages(ApiClient(), lang=args.lang))


def cmd_dcc(args):
    _print(tools.query_dcc_stats(ApiClient(), start_time=_ts(args.start), end_time=_ts(args.end)))



def build_parser():
    p = argparse.ArgumentParser(description="Carcolate-IM V2 OpenAPI 命令行工具")
    p.add_argument("--platform", default="whatsapp", choices=["whatsapp", "tiktok"],
                   help="平台（默认 whatsapp）")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("ts", help="时间字符串转毫秒时间戳")
    sp.add_argument("datetime", help="yyyy-MM-dd HH:mm")
    sp.set_defaults(func=cmd_ts)

    sp = sub.add_parser("accounts", help="平台账号列表")
    sp.set_defaults(func=cmd_accounts)

    sp = sub.add_parser("contacts", help="客户明细 / 搜索")
    sp.add_argument("--csr", type=int, help="分配客服 csrId")
    sp.add_argument("--keyword", help="模糊匹配 昵称/备注/手机号")
    sp.add_argument("--stage", help="stageKey 逗号分隔")
    sp.add_argument("--stage-level", dest="stage_level", help="按等级过滤（H/A/B/C/D）")
    sp.add_argument("--area", help="国家地区代码，如 CN")
    sp.add_argument("--link-accounts", dest="link_accounts", type=int, help="WA 账号 ID")
    sp.add_argument("--platform-account-id", dest="platform_account_id", type=int, help="平台账号ID")
    sp.add_argument("--id", type=int, help="客户ID（精确）")
    sp.add_argument("--nick", help="昵称（模糊）")
    sp.add_argument("--summary", help="会话总结关键字（模糊）")
    sp.add_argument("--start", help="firstSeen >= （时间戳或 yyyy-MM-dd HH:mm）")
    sp.add_argument("--end", help="firstSeen <= （时间戳或 yyyy-MM-dd HH:mm）")
    sp.add_argument("--last-seen-start", dest="last_seen_start", help="lastSeen >=")
    sp.add_argument("--last-seen-end", dest="last_seen_end", help="lastSeen <=")
    sp.add_argument("--lang", default="cn", help="cn / en")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=50)
    sp.set_defaults(func=cmd_contacts)

    sp = sub.add_parser("contact", help="按 contactId 取客户详情")
    sp.add_argument("id", type=int, help="客户ID")
    sp.add_argument("--lang", default="cn", help="cn / en")
    sp.set_defaults(func=cmd_contact)

    sp = sub.add_parser("messages", help="消息明细（contactId 必传，无分页）")
    sp.add_argument("--contact", type=int, required=True, help="客户ID（必填）")
    sp.add_argument("--start", required=True, help="起始时间")
    sp.add_argument("--end", required=True, help="结束时间")
    sp.add_argument("--csr", type=int, help="客服 csrId")
    sp.add_argument("--direction", help="inbound / outbound")
    sp.add_argument("--has-reply", dest="has_reply", help="true/false")
    sp.add_argument("--chat-only", dest="chat_only", action="store_true",
                    help="精简模式：仅返回 direction/textContent/csrName/sendTimeStr")
    sp.set_defaults(func=cmd_messages)

    sp = sub.add_parser("replies", help="回复明细")
    sp.add_argument("--start", required=True, help="起始时间")
    sp.add_argument("--end", required=True, help="结束时间")
    sp.add_argument("--csr", type=int, help="回复人 csrId")
    sp.add_argument("--contact", type=int, help="客户ID")
    sp.add_argument("--mode", help="copilot_accept_mode 逗号分隔")
    sp.add_argument("--keyword", help="模糊匹配 textContent / copilotSuggestion")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=50)
    sp.set_defaults(func=cmd_replies)

    sp = sub.add_parser("efficiency", help="回复时效聚合")
    sp.add_argument("--start", required=True, help="起始时间")
    sp.add_argument("--end", required=True, help="结束时间")
    sp.add_argument("--csr", type=int, help="客服 csrId")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=50)
    sp.set_defaults(func=cmd_efficiency)

    sp = sub.add_parser("distribution", help="客户检索条件分布")
    sp.add_argument("--csr", type=int, help="分配客服 csrId")
    sp.add_argument("--stage", help="stageKey 逗号分隔")
    sp.add_argument("--stage-level", dest="stage_level", help="按等级过滤（H/A/B/C/D）")
    sp.add_argument("--platform-account-id", dest="platform_account_id", type=int)
    sp.add_argument("--lang", default="cn", help="cn / en")
    sp.set_defaults(func=cmd_distribution)

    sp = sub.add_parser("csrs", help="客服列表")
    sp.set_defaults(func=cmd_csrs)

    sp = sub.add_parser("stages", help="标签字典")
    sp.add_argument("--lang", default="cn", help="cn / en")
    sp.set_defaults(func=cmd_stages)

    sp = sub.add_parser("dcc", help="DCC 看板统计")
    sp.add_argument("--start", required=True, help="起始时间")
    sp.add_argument("--end", required=True, help="结束时间")
    sp.set_defaults(func=cmd_dcc)

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
