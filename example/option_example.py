"""
行情接口验证脚本 - 调用 market.py 和 optmarket.py 验证接口
运行前请先执行: pip install -e .

期权接口支持单独或组合调用，通过 --opt-api 指定：
  python option_example.py --opt-api orderbook --opt-code "usAAPL 20260320 270.0 CALL"
  python option_example.py --opt-api kline --opt-code "usAAPL 20260320 270.0 CALL" --kline-ktype day --kline-num 10
  python option_example.py --opt-api quote --quote-codes "code1,code2" --quote-fields last,bid,ask
  python option_example.py --opt-api kline,quote,tick --opt-code "usAAPL 20260320 270.0 CALL"
  python option_example.py --opt-api all  # 调用全部 5 个期权接口
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
DEFAULT_MARKET_CODE = "hk00700"           # 港股腾讯
DEFAULT_OPT_CODE = "usAAPL 20260320 270.0 CALL"   # 美股苹果期权

# 期权 5 个接口名称，用于 --opt-api 参数
OPT_API_NAMES = ("orderbook", "kline", "quote", "tick", "day_min")

client = SDKClient(BASE_URL, API_KEY)
# print(f"BASE_URL: {BASE_URL}")
# print(f"API_KEY: {API_KEY}")


def ensure_session():
    # print("已创建新会话")
    print("\n===== 1. 会话管理 =====")
    # session.json 通过 dump_session() 保存，包含 clientPrivateKey，
    # 下次启动时可用 restore_session() 重新派生双密钥，跳过握手。
    session_file = '../session.json'
    restored = False

    print(f"session_file: {os.path.exists(session_file)}")
    if os.path.exists(session_file):
        print(f"session_file exists")
        with open(session_file, 'r', encoding='utf-8') as f:
            print(f"cached: {f}")
            cached = json.load(f)
        if client.restore_session(cached):
            print("已从本地 ./session.json 恢复有效会话，跳过握手。")
            restored = True
        else:
            print("本地会话已过期，需重新创建。")

    if not restored:
        print(f"create session")
        client.session.create_session()
        dumped = client.dump_session()   # 包含 clientPrivateKey，可完整恢复
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(dumped, f, ensure_ascii=False, indent=2)
        print("已创建新会话并保存到 ./session.json")

    current = client.session.query_session()
    print("查询当前会话:", current)

    if client.session.is_session_valid():
        print("会话状态: 有效")

    # 主动登出（演示用，实际按需调用）
    # client.session.delete_session()


def print_response(r):
    """打印完整响应，包含所有参数（code、message、requestId、data 等）"""
    print("  响应:", json.dumps(r, ensure_ascii=False, indent=2, default=str))


def verify_market(market_code):
    """验证证券行情接口"""
    print("\n" + "=" * 50)
    print("证券行情 (market)")
    print("=" * 50)

    # 1. 批量报价
    print("\n[1] 批量报价 quote")
    r = client.market.quote(codes=[market_code])
    print_response(r)

    # 2. K 线
    print("\n[2] K 线 kline")
    r = client.market.kline(market_code, ktype="day", num=5)
    print_response(r)

    # 3. 分时
    print("\n[3] 分时 min")
    r = client.market.min(market_code, count=5)
    print_response(r)

    # 4. 盘口
    print("\n[4] 盘口 orderbook")
    r = client.market.orderbook(market_code, count=5)
    print_response(r)

    # 5. 逐笔成交
    print("\n[5] 逐笔成交 tick")
    r = client.market.tick(market_code, count=10, id=-1)
    print_response(r)

    # 6. 经纪商队列
    print("\n[6] 经纪商队列 broker_list")
    r = client.market.broker_list(market_code)
    print_response(r)

    print("\n证券行情接口验证完成 ✓")


def verify_optmarket(opts, apis=None):
    """验证期权行情接口，opts 为参数字典，apis 为要调用的接口名列表（默认全部）"""
    opt_code = opts.get("opt_code")
    kline_ktype = opts.get("kline_ktype", "1")
    kline_num = opts.get("kline_num", 5)
    kline_end_time = opts.get("kline_end_time")
    kline_interval = opts.get("kline_interval")
    kline_start_time = opts.get("kline_start_time")
    kline_suspension = opts.get("kline_suspension")
    kline_time = opts.get("kline_time")
    tick_count = opts.get("tick_count", 10)
    tick_id = opts.get("tick_id", -1)
    day_min_num = opts.get("day_min_num", 3)
    quote_codes = opts.get("quote_codes")
    quote_fields = opts.get("quote_fields")

    if apis is None:
        apis = list(OPT_API_NAMES)

    print("\n" + "=" * 50)
    print("期权行情 (optmarket)")
    print("=" * 50)

    if "orderbook" in apis:
        print("\n[1] 期权盘口 orderbook")
        r = client.optmarket.orderbook(opt_code)
        print_response(r)

    if "kline" in apis:
        print("\n[2] 期权 K 线 kline")
        r = client.optmarket.kline(
            opt_code,
            ktype=kline_ktype,
            num=kline_num,
            end_time=kline_end_time,
            interval=kline_interval,
            start_time=kline_start_time,
            suspension=kline_suspension,
            time=kline_time,
        )
        print_response(r)

    if "quote" in apis:
        print("\n[3] 期权批量报价 quote")
        codes = quote_codes if quote_codes else [opt_code]
        r = client.optmarket.quote(codes=codes, fields=quote_fields)
        print_response(r)

    if "tick" in apis:
        print("\n[4] 期权逐笔 tick")
        r = client.optmarket.tick(opt_code, count=tick_count, id=tick_id)
        print_response(r)

    if "day_min" in apis:
        print("\n[5] 期权多日分时 day_min")
        r = client.optmarket.day_min(opt_code, num=day_min_num)
        print_response(r)

    print("\n期权行情接口验证完成 ✓")


def parse_args():
    """解析命令行参数"""
    p = argparse.ArgumentParser(description="行情接口验证脚本")
    p.add_argument("--market-code", default=DEFAULT_MARKET_CODE, help="证券代码，如 hk00700")
    p.add_argument("--opt-code", default=DEFAULT_OPT_CODE, help="期权代码，如 usAAPL 20260320 270.0 CALL")
    p.add_argument("--opt-only", action="store_true", help="仅验证期权接口（调用全部 5 个）")
    p.add_argument(
        "--opt-api",
        metavar="API",
        help="期权接口：orderbook/kline/quote/tick/day_min，逗号分隔或 all。指定后仅调用所列接口",
    )
    # 期权接口参数
    p.add_argument("--kline-ktype", default="1", help="K 线类型，如 1/5/15/day")
    p.add_argument("--kline-num", type=int, default=5, help="K 线数量")
    p.add_argument("--kline-time", type=int, help="K 线时间戳")
    p.add_argument("--kline-start-time", type=int, help="K 线开始时间戳")
    p.add_argument("--kline-end-time", type=int, help="K 线结束时间戳")
    p.add_argument("--kline-interval", type=int, help="K 线间隔")
    p.add_argument("--kline-suspension", type=int, help="K 线停牌处理")
    p.add_argument("--tick-count", type=int, default=10, help="逐笔成交数量 (-500~500)")
    p.add_argument("--tick-id", type=int, default=-1, help="逐笔成交起始 id，-1 表示最新")
    p.add_argument("--day-min-num", type=int, default=3, help="多日分时天数 (1~10)")
    p.add_argument("--quote-codes", help="批量报价代码，逗号分隔，不填则用 opt-code")
    p.add_argument("--quote-fields", help="批量报价返回字段，逗号分隔，如 last,bid,ask,volume")
    return p.parse_args()


def parse_opt_apis(opt_api_arg, opt_only):
    """解析要调用的期权接口列表。返回 (apis, run_market)"""
    if opt_api_arg is not None:
        # --opt-api 指定时，仅跑期权，跳过证券行情
        raw = [x.strip().lower() for x in opt_api_arg.split(",") if x.strip()]
        if "all" in raw:
            return list(OPT_API_NAMES), False
        apis = [a for a in raw if a in OPT_API_NAMES]
        if not apis:
            raise SystemExit(f"无效的 --opt-api: {opt_api_arg}，可选: {', '.join(OPT_API_NAMES)}, all")
        return apis, False
    if opt_only:
        return list(OPT_API_NAMES), False
    # 默认：跑证券行情 + 全部 5 个期权接口
    return list(OPT_API_NAMES), True


if __name__ == "__main__":
    args = parse_args()
    try:
        opt_apis, run_market = parse_opt_apis(args.opt_api, args.opt_only)
    except SystemExit as e:
        raise e

    opt_opts = {
        "opt_code": args.opt_code,
        "kline_ktype": args.kline_ktype,
        "kline_num": args.kline_num,
        "kline_time": args.kline_time,
        "kline_start_time": args.kline_start_time,
        "kline_end_time": args.kline_end_time,
        "kline_interval": args.kline_interval,
        "kline_suspension": args.kline_suspension,
        "tick_count": args.tick_count,
        "tick_id": args.tick_id,
        "day_min_num": args.day_min_num,
        "quote_codes": [c.strip() for c in args.quote_codes.split(",")] if args.quote_codes else None,
        "quote_fields": [f.strip() for f in args.quote_fields.split(",")] if args.quote_fields else None,
    }
    try:
        print(f"ensure_session")
        ensure_session()
        if run_market:
            verify_market(args.market_code)
        verify_optmarket(opt_opts, apis=opt_apis)
        print("\n" + "=" * 50)
        print("全部接口验证通过")
        print("=" * 50)
    except AuthenticationError as e:
        print_response({"code": e.code, "message": e.message, "requestId": e.request_id, "data": getattr(e, "data", None)})
    except PermissionError as e:
        print_response({"code": e.code, "message": e.message, "requestId": e.request_id, "data": getattr(e, "data", None)})
    except APIError as e:
        print_response({"code": e.code, "message": e.message, "requestId": e.request_id, "data": getattr(e, "data", None)})
