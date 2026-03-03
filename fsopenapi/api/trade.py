class TradeAPI:
    def __init__(self, client):
        self.client = client

    def create_order(
        self,
        sub_account_id,
        stock_code,
        direction,
        order_type,
        quantity,
        price=None,
        market_code="hk",
        currency="HKD",
        client_id=None,
        allow_pre_post=None,
        exp_type=None,
        expiry_date=None,
        short_sell_type=None,
        trig_price=None,
        tail_type=None,
        tail_amount=None,
        tail_pct=None,
        spread=None,
    ):
        """下单"""
        payload = {
            "subAccountId": str(sub_account_id),
            "stockCode": str(stock_code),
            "direction": int(direction),
            "orderType": int(order_type),
            "quantity": str(quantity),
            "marketCode": str(market_code),
            "currency": str(currency),
        }
        if price is not None:
            payload["price"] = str(price)
        if client_id is not None:
            payload["clientId"] = int(client_id)
        if allow_pre_post is not None:
            payload["allowPrePost"] = int(allow_pre_post)
        if exp_type is not None:
            payload["expType"] = int(exp_type)
        if expiry_date is not None:
            payload["expiryDate"] = str(expiry_date)
        if short_sell_type is not None:
            payload["shortSellType"] = str(short_sell_type)
        if trig_price is not None:
            payload["trigPrice"] = str(trig_price)
        if tail_type is not None:
            payload["tailType"] = int(tail_type)
        if tail_amount is not None:
            payload["tailAmount"] = str(tail_amount)
        if tail_pct is not None:
            payload["tailPct"] = str(tail_pct)
        if spread is not None:
            payload["spread"] = str(spread)
        return self.client.post("/api/v1/trade/OrderCreate", data=payload)

    def cancel_order(self, order_id, sub_account_id=None, client_id=None):
        """撤单"""
        payload = {"orderId": str(order_id)}
        if sub_account_id is not None:
            payload["subAccountId"] = str(sub_account_id)
        if client_id is not None:
            payload["clientId"] = int(client_id)
        return self.client.post("/api/v1/trade/OrderCancel", data=payload)

    def list_orders(
        self,
        sub_account_id,
        start=0,
        count=20,
        stock_code=None,
        status_arr=None,
        from_date=None,
        to_date=None,
        direction=None,
        market=None,
        sort="desc",
        client_id=None,
    ):
        """查询订单列表

        Args:
            sub_account_id: 证券账户（必填）
            start: 偏移量（mapping start）
            count: 返回数量（mapping count）
            stock_code: 股票代码（可选）
            status_arr: 订单状态筛选，trade-core 枚举，如 [20, 40]；不传返回所有
            from_date: 开始日期 yyyy-mm-dd（可选）
            to_date: 结束日期 yyyy-mm-dd（可选）
            direction: 方向 1买 2卖（可选）
            market: 市场列表如 ["hk","us"]（可选）
            sort: desc/asc，默认 desc
            client_id: 客户 ID（可选）
        """
        payload = {
            "subAccountId": str(sub_account_id),
            "start": int(start),
            "count": int(count),
            "sort": str(sort),
        }
        if stock_code:
            payload["stockCode"] = str(stock_code)
        if status_arr is not None:
            payload["statusArr"] = [int(x) for x in list(status_arr)]
        if from_date is not None:
            payload["fromDate"] = from_date
        if to_date is not None:
            payload["toDate"] = to_date
        if direction is not None:
            payload["direction"] = int(direction)
        if market is not None:
            _m = market if isinstance(market, list) else [market]
            payload["market"] = [str(x) for x in _m]
        if client_id is not None:
            payload["clientId"] = int(client_id)
        return self.client.post("/api/v1/trade/OrderList", data=payload)

    def get_cash_flows(self, sub_account_id, trade_date_from=None, trade_date_to=None, flow_type=None, business_type=None, date=None):
        """查询资金流水"""
        payload = {"subAccountId": str(sub_account_id)}
        if trade_date_from is not None:
            payload["tradeDateFrom"] = trade_date_from
        if trade_date_to is not None:
            payload["tradeDateTo"] = trade_date_to
        if flow_type is not None:
            payload["flowType"] = int(flow_type)
        if business_type is not None:
            _bt = business_type if isinstance(business_type, list) else [business_type]
            payload["businessType"] = [int(x) for x in _bt]
        if date is not None:
            payload["date"] = date
        return self.client.post("/api/v1/trade/CashFlows", data=payload)

    def get_bid_ask_info(
        self,
        sub_account_id,
        stock_code,
        order_type=3,
        market_code="hk",
        quantity=None,
        price=None,
        trig_price=None,
        direction=1,
        client_id=None,
    ):
        """查询买卖信息"""
        payload = {
            "subAccountId": str(sub_account_id),
            "stockCode": str(stock_code),
            "orderType": int(order_type),
            "marketCode": str(market_code),
            "direction": int(direction),
        }
        if quantity is not None:
            payload["quantity"] = str(quantity)
        if price is not None:
            payload["price"] = str(price)
        if trig_price is not None:
            payload["trigPrice"] = str(trig_price)
        if client_id is not None:
            payload["clientId"] = int(client_id)
        return self.client.post("/api/v1/trade/BidAskInfo", data=payload)
