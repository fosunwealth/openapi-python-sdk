"""
Fosun Wealth OpenAPI Python SDK - 使用示例
运行前请先执行: pip install -e .
"""

import json
import logging
import os

from fsopenapi import APIError, AuthenticationError, CacheError, JsonFormatter, PermissionError, SDKClient

# ============================================================
# 配置：替换为实际的网关地址和 API Key
# ============================================================
SUB_ACCOUNT_ID = "xxxx"
WEBHOOK_ENDPOINT = "https://your-partner-host/webhook"

# 可选：ops 环境设置 SDK_TYPE=ops，SDK 会自动改走 /api/ops/v1/... 前缀
# os.environ["SDK_TYPE"] = "ops"


def build_demo_logger():
    logger = logging.getLogger("demo.fsopenapi")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


client = SDKClient(
    logger=build_demo_logger(),
    logging_enable=True,
    log_body=False,
)


def demo_session():
    print("\n===== 1. 会话管理 =====")
    # session.json 通过 dump_session() 保存，包含 clientPrivateKey，
    # 下次启动时可用 restore_session() 重新派生双密钥，跳过握手。
    session_file = '../session.json'
    restored = False

    if os.path.exists(session_file):
        with open(session_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        if client.restore_session(cached):
            print("已从本地 ./session.json 恢复有效会话，跳过握手。")
            restored = True
        else:
            print("本地会话已过期，需重新创建。")

    if not restored:
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


def demo_account():
    print("\n===== 2. 账户 =====")
    accounts = client.account.list_accounts()
    print("账户列表:", accounts)


def demo_portfolio():
    print("\n===== 3. 组合 =====")
    summary = client.portfolio.get_assets_summary(sub_account_id=SUB_ACCOUNT_ID)
    print("资金汇总:", summary)

    holdings = client.portfolio.get_holdings(
        sub_account_id=SUB_ACCOUNT_ID,
        start=0,
        count=100,
        product_types=[1, 2],
        currencies=["HKD", "USD"],
    )
    print("持仓列表:", holdings)


def demo_trade():
    print("\n===== 4. 交易 =====")

    # 下单（限价单）
    order = client.trade.create_order(
        sub_account_id=SUB_ACCOUNT_ID,
        stock_code="00700",
        direction=1,        # 1 买 / 2 卖
        order_type=1,       # 1 限价
        quantity="100",
        price="350.00",
        market_code="hk",
        currency="HKD",
    )
    print("下单结果:", order)

    order_id = order.get("orderId") if order else None

    # 改单（普通订单参数修改）
    if order_id:
        modify_result = client.trade.order_modify(
            sub_account_id=SUB_ACCOUNT_ID,
            order_id=order_id,
            modify_type=1,  # 1 修改普通订单参数，2 修改条件单参数
            quantity="100",
            price="351.00",
        )
        print("改单结果:", modify_result)

    # 撤单
    if order_id:
        cancel_result = client.trade.cancel_order(
            order_id=order_id,
            sub_account_id=SUB_ACCOUNT_ID,
        )
        print("撤单结果:", cancel_result)

    # 订单列表
    orders = client.trade.list_orders(
        sub_account_id=SUB_ACCOUNT_ID,
        start=0,
        count=20,
        status_arr=[20, 40],
        from_date="2025-01-01",
        to_date="2025-01-31",
    )
    print("订单列表:", orders)

    # 资金流水
    flows = client.trade.get_cash_flows(
        sub_account_id=SUB_ACCOUNT_ID,
        trade_date_from="2025-01-01",
        trade_date_to="2025-01-31",
    )
    print("资金流水:", flows)

    # 买卖信息（下单前校验）
    bid_ask = client.trade.get_bid_ask_info(
        sub_account_id=SUB_ACCOUNT_ID,
        stock_code="00700",
        order_type=3,
        market_code="hk",
        quantity="100",
        direction=1,
    )
    print("买卖信息:", bid_ask)


def demo_subscription():
    print("\n===== 5. 交易订阅 =====")

    # 当前仅暴露 orderUpdate 订阅
    created = client.trade.create_subscription(
        event_type="orderUpdate",
        endpoint=WEBHOOK_ENDPOINT,
    )
    print("创建订阅:", created)

    subscriptions = client.trade.list_subscriptions(start=0, count=20)
    print("订阅列表:", subscriptions)

    subscription_id = None
    data = created.get("data") if isinstance(created, dict) else None
    if isinstance(data, dict):
        subscription_id = data.get("subscriptionId")

    if subscription_id:
        updated = client.trade.update_subscription(
            subscription_id=subscription_id,
            endpoint=f"{WEBHOOK_ENDPOINT}/v2",
        )
        print("更新订阅:", updated)

        deleted = client.trade.delete_subscription(subscription_id=subscription_id)
        print("删除订阅:", deleted)


def demo_market():
    print("\n===== 6. 行情 =====")

    # 批量报价（codes 格式: marketCode + stockCode）
    quote = client.market.quote(codes=["hk00700", "usAAPL"])
    print("批量报价:", quote)

    # K 线
    klines = client.market.kline("hk00700", ktype="day", num=30)
    print("K 线:", klines)

    # 分时
    min_data = client.market.min("hk00700", count=5)
    print("分时:", min_data)

    # 盘口/买卖档
    orderbook = client.market.orderbook("hk00700", count=5)
    print("盘口:", orderbook)

    # 逐笔成交
    ticks = client.market.tick("hk00700", count=20, id=-1)
    print("逐笔成交:", ticks)

    # 买卖盘经纪商队列
    brokers = client.market.broker_list("hk00700")
    print("经纪商队列:", brokers)


if __name__ == "__main__":
    try:
        demo_session()
        demo_account()
        demo_portfolio()
        demo_trade()
        demo_subscription()
        demo_market()
    except AuthenticationError as e:
        print(f"鉴权失败: {e.code} - {e.message}")
    except PermissionError as e:
        print(f"权限错误: {e.code} - {e.message}")
    except CacheError as e:
        print(f"缓存错误: {e.code} - {e.message}")
    except APIError as e:
        print(f"接口错误: {e.code} - {e.message} (requestId: {e.request_id})")
