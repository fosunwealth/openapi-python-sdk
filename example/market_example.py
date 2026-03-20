"""
证券行情接口验证脚本 - 调用 market.py 六个接口验证
运行前请先执行: pip install -e .

支持单独或组合调用，通过 --api 指定：
  python market_example.py --api quote --market-code hk00700
  python market_example.py --api kline,quote,tick --market-code hk00700
  python market_example.py --api all  # 调用全部 6 个证券行情接口

六个接口的可选参数均支持通过命令行传入（不传则使用默认值）：
  quote:     --quote-fields
  kline:     --kline-ktype, --kline-num, --kline-delay, --kline-time, --kline-start-time, --kline-end-time, --kline-right, --kline-suspension
  min:       --min-count
  orderbook: --orderbook-count
  tick:      --tick-count, --tick-id, --tick-ts
"""

from fsopenapi import SDKClient, APIError, AuthenticationError, PermissionError
import argparse
import json
import os

# ============================================================
# 配置：替换为实际的网关地址和 API Key
# ============================================================
BASE_URL = os.environ.get("FSOPENAPI_BASE_URL", "xxx")
API_KEY = os.environ.get("FSOPENAPI_API_KEY", "your_api_key")

# 默认证券代码（可替换为实际可用的代码）
DEFAULT_MARKET_CODE = "hk00700"  # 港股腾讯

# 证券行情 6 个接口名称，用于 --api 参数
MARKET_API_NAMES = ("quote", "kline", "min", "orderbook", "tick", "broker_list")

client = SDKClient(BASE_URL, API_KEY)


def ensure_session():
    """创建或恢复会话，完成鉴权"""
    print("\n===== 1. 会话管理 =====")
    session_file = "../session.json"
    restored = False

    if os.path.exists(session_file):
        with open(session_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        if client.restore_session(cached):
            print("已从本地 ./session.json 恢复有效会话，跳过握手。")
            restored = True
        else:
            print("本地会话已过期，需重新创建。")

    if not restored:
        client.session.create_session()
        dumped = client.dump_session()
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(dumped, f, ensure_ascii=False, indent=2)
        print("已创建新会话并保存到 ./session.json")

    current = client.session.query_session()
    print("查询当前会话:", current)

    if client.session.is_session_valid():
        print("会话状态: 有效")


def print_response(r):
    """打印完整响应，包含所有参数（code、message、requestId、data 等）"""
    print("  响应:", json.dumps(r, ensure_ascii=False, indent=2, default=str))


def verify_market(market_code, apis=None, opts=None):
    """验证证券行情接口，apis 为要调用的接口名列表（默认全部），opts 为可选参数字典"""
    if apis is None:
        apis = list(MARKET_API_NAMES)
    opts = opts or {}

    print("\n" + "=" * 50)
    print("证券行情 (market)")
    print("=" * 50)

    if "quote" in apis:
        print("\n[1] 批量报价 quote")
        kw = {"codes": [market_code]}
        if opts.get("quote_fields") is not None:
            kw["fields"] = opts["quote_fields"]
        r = client.market.quote(**kw)
        print_response(r)

    if "kline" in apis:
        print("\n[2] K 线 kline")
        kw = {"code": market_code, "ktype": opts.get("kline_ktype", "day")}
        if opts.get("kline_num") is not None:
            kw["num"] = opts["kline_num"]
        if opts.get("kline_delay") is not None:
            kw["delay"] = opts["kline_delay"]
        if opts.get("kline_time") is not None:
            kw["time"] = opts["kline_time"]
        if opts.get("kline_start_time") is not None:
            kw["start_time"] = opts["kline_start_time"]
        if opts.get("kline_end_time") is not None:
            kw["end_time"] = opts["kline_end_time"]
        if opts.get("kline_right") is not None:
            kw["right"] = opts["kline_right"]
        if opts.get("kline_suspension") is not None:
            kw["suspension"] = opts["kline_suspension"]
        r = client.market.kline(**kw)
        print_response(r)

    if "min" in apis:
        print("\n[3] 分时 min")
        kw = {"code": market_code}
        if opts.get("min_count") is not None:
            kw["count"] = opts["min_count"]
        r = client.market.min(**kw)
        print_response(r)

    if "orderbook" in apis:
        print("\n[4] 盘口 orderbook")
        kw = {"code": market_code}
        if opts.get("orderbook_count") is not None:
            kw["count"] = opts["orderbook_count"]
        r = client.market.orderbook(**kw)
        print_response(r)

    if "tick" in apis:
        print("\n[5] 逐笔成交 tick")
        kw = {"code": market_code}
        if opts.get("tick_count") is not None:
            kw["count"] = opts["tick_count"]
        if opts.get("tick_id") is not None:
            kw["id"] = opts["tick_id"]
        if opts.get("tick_ts") is not None:
            kw["ts"] = opts["tick_ts"]
        r = client.market.tick(**kw)
        print_response(r)

    if "broker_list" in apis:
        print("\n[6] 经纪商队列 broker_list")
        r = client.market.broker_list(market_code)
        print_response(r)

    print("\n证券行情接口验证完成 ✓")


def parse_args():
    """解析命令行参数"""
    p = argparse.ArgumentParser(description="证券行情接口验证脚本")
    p.add_argument("--market-code", default=DEFAULT_MARKET_CODE, help="证券代码，如 hk00700")
    p.add_argument(
        "--api",
        metavar="API",
        help="接口：quote/kline/min/orderbook/tick/broker_list，逗号分隔或 all。指定后仅调用所列接口",
    )
    # quote 可选参数
    p.add_argument("--quote-fields", nargs="+", metavar="F", help="quote: 指定返回字段，如 last bid ask")
    # kline 可选参数
    p.add_argument("--kline-ktype", default="day", help="kline: K 线类型，如 day/5/15，默认 day")
    p.add_argument("--kline-num", type=int, metavar="N", help="kline: 返回条数")
    p.add_argument("--kline-delay", type=lambda x: x.lower() in ("1", "true", "yes"), metavar="BOOL", help="kline: 是否延迟")
    p.add_argument("--kline-time", type=int, metavar="TS", help="kline: 时间戳")
    p.add_argument("--kline-start-time", type=int, metavar="TS", help="kline: 开始时间戳")
    p.add_argument("--kline-end-time", type=int, metavar="TS", help="kline: 结束时间戳")
    p.add_argument("--kline-right", metavar="S", help="kline: 复权方式")
    p.add_argument("--kline-suspension", type=int, metavar="N", help="kline: 停牌处理")
    # min 可选参数
    p.add_argument("--min-count", type=int, metavar="N", help="min: 返回点数，默认 5")
    # orderbook 可选参数
    p.add_argument("--orderbook-count", type=int, metavar="N", help="orderbook: 档位数量，默认 5")
    # tick 可选参数
    p.add_argument("--tick-count", type=int, metavar="N", help="tick: 返回条数，默认 20")
    p.add_argument("--tick-id", type=int, metavar="N", help="tick: 起始 tick id，-1 表示最新")
    p.add_argument("--tick-ts", metavar="S", help="tick: 时间戳")
    return p.parse_args()


def parse_apis(api_arg):
    """解析要调用的接口列表"""
    if api_arg is None:
        return list(MARKET_API_NAMES)
    raw = [x.strip().lower() for x in api_arg.split(",") if x.strip()]
    if "all" in raw:
        return list(MARKET_API_NAMES)
    apis = [a for a in raw if a in MARKET_API_NAMES]
    if not apis:
        raise SystemExit(
            f"无效的 --api: {api_arg}，可选: {', '.join(MARKET_API_NAMES)}, all"
        )
    return apis


def build_opts(args):
    """从命令行参数构建 opts 字典，仅包含用户显式传入的可选参数"""
    opts = {}
    if args.quote_fields is not None:
        opts["quote_fields"] = args.quote_fields
    if args.kline_ktype is not None:
        opts["kline_ktype"] = args.kline_ktype
    if args.kline_num is not None:
        opts["kline_num"] = args.kline_num
    if args.kline_delay is not None:
        opts["kline_delay"] = args.kline_delay
    if args.kline_time is not None:
        opts["kline_time"] = args.kline_time
    if args.kline_start_time is not None:
        opts["kline_start_time"] = args.kline_start_time
    if args.kline_end_time is not None:
        opts["kline_end_time"] = args.kline_end_time
    if args.kline_right is not None:
        opts["kline_right"] = args.kline_right
    if args.kline_suspension is not None:
        opts["kline_suspension"] = args.kline_suspension
    if args.min_count is not None:
        opts["min_count"] = args.min_count
    if args.orderbook_count is not None:
        opts["orderbook_count"] = args.orderbook_count
    if args.tick_count is not None:
        opts["tick_count"] = args.tick_count
    if args.tick_id is not None:
        opts["tick_id"] = args.tick_id
    if args.tick_ts is not None:
        opts["tick_ts"] = args.tick_ts
    return opts


if __name__ == "__main__":
    args = parse_args()
    try:
        apis = parse_apis(args.api)
    except SystemExit as e:
        raise e

    opts = build_opts(args)

    try:
        ensure_session()
        verify_market(args.market_code, apis=apis, opts=opts)
        print("\n" + "=" * 50)
        print("全部接口验证通过")
        print("=" * 50)
    except AuthenticationError as e:
        print_response({"code": e.code, "message": e.message, "requestId": e.request_id, "data": getattr(e, "data", None)})
    except PermissionError as e:
        print_response({"code": e.code, "message": e.message, "requestId": e.request_id, "data": getattr(e, "data", None)})
    except APIError as e:
        print_response({"code": e.code, "message": e.message, "requestId": e.request_id, "data": getattr(e, "data", None)})
