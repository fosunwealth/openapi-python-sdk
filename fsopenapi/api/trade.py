_ALLOWED_SUBSCRIPTION_EVENT_TYPES = {"orderUpdate"}


def _normalize_subscription_event_type(event_type):
    if event_type is None:
        raise ValueError("event_type is required")
    normalized = str(event_type).strip()
    if not normalized:
        raise ValueError("event_type is required")
    if normalized not in _ALLOWED_SUBSCRIPTION_EVENT_TYPES:
        raise ValueError("event_type currently only supports: orderUpdate")
    return normalized


def _normalize_required_string(value, field_name):
    if value is None:
        raise ValueError(f"{field_name} is required")
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _normalize_required_int(value, field_name):
    if value is None:
        raise ValueError(f"{field_name} is required")
    return int(value)


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
        time_in_force=None,
        exp_type=None,
        short_sell_type=None,
        trig_price=None,
        tail_type=None,
        tail_amount=None,
        tail_pct=None,
        spread=None,
        profit_trig_price=None,
        profit_quantity=None,
        stop_loss_trig_price=None,
        stop_loss_quantity=None,
        product_type=None,
        expiry=None,
        strike=None,
        right=None,
        apply_account_id=None,
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
        if time_in_force is not None:
            payload["timeInForce"] = int(time_in_force)
        if exp_type is not None:
            payload["expType"] = int(exp_type)
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
        if profit_trig_price is not None:
            payload["profitPrice"] = str(profit_trig_price)
        if profit_quantity is not None:
            payload["profitQuantity"] = str(profit_quantity)
        if stop_loss_trig_price is not None:
            payload["stopLossPrice"] = str(stop_loss_trig_price)
        if stop_loss_quantity is not None:
            payload["stopLossQuantity"] = str(stop_loss_quantity)
        if product_type is not None:
            payload["productType"] = int(product_type)
        if expiry is not None:
            payload["expiry"] = str(expiry)
        if strike is not None:
            payload["strike"] = str(strike)
        if right is not None:
            payload["right"] = str(right)
        if apply_account_id is not None:
            payload["applyAccountId"] = str(apply_account_id)
        return self.client.post("/v1/trade/OrderCreate", data=payload)

    def cancel_order(self, order_id, sub_account_id=None, client_id=None, product_type=None, apply_account_id=None):
        """撤单"""
        payload = {"orderId": str(order_id)}
        if sub_account_id is not None:
            payload["subAccountId"] = str(sub_account_id)
        if client_id is not None:
            payload["clientId"] = int(client_id)
        if product_type is not None:
            payload["productType"] = int(product_type)  
        if apply_account_id is not None:
            payload["applyAccountId"] = str(apply_account_id)
        return self.client.post("/v1/trade/OrderCancel", data=payload)

    def order_modify(
        self,
        sub_account_id,
        order_id,
        modify_type,
        client_id=None,
        quantity=None,
        price=None,
        trig_price=None,
        tail_type=None,
        tail_amount=None,
        tail_pct=None,
        spread=None,
        profit_trig_price=None,
        profit_quantity=None,
        stop_loss_trig_price=None,
        stop_loss_quantity=None,
        product_type=None,
        apply_account_id=None,
    ):
        """改单"""
        payload = {
            "subAccountId": str(sub_account_id),
            "orderId": str(order_id),
            "modifyType": int(modify_type),
        }
        if client_id is not None:
            payload["clientId"] = int(client_id)
        if quantity is not None:
            payload["quantity"] = str(quantity)
        if price is not None:
            payload["price"] = str(price)
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
        if profit_trig_price is not None:
            payload["profitPrice"] = str(profit_trig_price)
        if profit_quantity is not None:
            payload["profitQuantity"] = str(profit_quantity)
        if stop_loss_trig_price is not None:
            payload["stopLossPrice"] = str(stop_loss_trig_price)
        if stop_loss_quantity is not None:
            payload["stopLossQuantity"] = str(stop_loss_quantity)
        if product_type is not None:
            payload["productType"] = int(product_type)
        if apply_account_id is not None:
            payload["applyAccountId"] = str(apply_account_id)
        return self.client.post("/v1/trade/OrderModify", data=payload)

    def create_subscription(self, event_type, endpoint, channel_type=1):
        """创建交易订阅"""
        payload = {
            "eventType": _normalize_subscription_event_type(event_type),
            "channelType": int(channel_type),
            "endpoint": _normalize_required_string(endpoint, "endpoint"),
        }
        return self.client.post("/v1/trade/SubscriptionCreate", data=payload)

    def update_subscription(self, subscription_id, endpoint):
        """更新订阅回调地址"""
        payload = {
            "subscriptionId": _normalize_required_int(
                subscription_id, "subscription_id"
            ),
            "endpoint": _normalize_required_string(endpoint, "endpoint"),
        }
        return self.client.post("/v1/trade/SubscriptionUpdate", data=payload)

    def delete_subscription(self, subscription_id):
        """删除订阅"""
        payload = {
            "subscriptionId": _normalize_required_int(
                subscription_id, "subscription_id"
            )
        }
        return self.client.post("/v1/trade/SubscriptionDelete", data=payload)

    def list_subscriptions(self, start=0, count=20, event_type=None):
        """查询订阅列表"""
        payload = {
            "start": int(start),
            "count": int(count),
        }
        if event_type is not None:
            payload["eventType"] = _normalize_subscription_event_type(event_type)
        return self.client.post("/v1/trade/SubscriptionList", data=payload)

    def list_orders(
        self,
        sub_account_id,
        apply_account_id=None,
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
        show_type=None,
    ):
        """查询订单列表"""
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
        if apply_account_id is not None:
            payload["applyAccountId"] = str(apply_account_id)
        if show_type is not None:
            payload["showType"] = int(show_type)
        return self.client.post("/v1/trade/OrderList", data=payload)

    def get_cash_flows(
        self,
        sub_account_id,
        trade_date_from=None,
        trade_date_to=None,
        flow_type=None,
        business_type=None,
        date=None,
        apply_account_id=None,
        sub_account_class=None,
    ):
        """查询资金流水"""
        payload = {"subAccountId": str(sub_account_id)}
        if apply_account_id is not None:
            payload["applyAccountId"] = str(apply_account_id)
        if sub_account_class is not None:
            payload["subAccountClass"] = int(sub_account_class)
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
        return self.client.post("/v1/trade/CashFlows", data=payload)

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
        product_type=None,
        expiry=None,
        strike=None,
        right=None,
        time_in_force=None,
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
        if product_type is not None:
            payload["productType"] = int(product_type)
        if expiry is not None:
            payload["expiry"] = str(expiry)
        if strike is not None:
            payload["strike"] = str(strike)
        if right is not None:
            payload["right"] = str(right)
        if time_in_force is not None:
            payload["timeInForce"] = int(time_in_force)
        return self.client.post("/v1/trade/BidAskInfo", data=payload)
