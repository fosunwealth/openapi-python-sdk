# 行情 API

class MarketAPI:
    def __init__(self, client):
        self.client = client

    def quote(self, codes, delay=None, fields=None):
        """批量证券报价
        """
        payload = {"codes": list(codes)}
        if delay is not None:
            payload["delay"] = bool(delay)
        if fields is not None:
            payload["fields"] = list(fields)
        return self.client.post("/api/v1/market/secu/quote", data=payload)

    def kline(
        self,
        code,
        ktype,
        delay=None,
        end_time=None,
        num=None,
        right=None,
        start_time=None,
        suspension=None,
        time=None,
    ):
        """K 线
        """
        payload = {"code": code, "ktype": ktype}
        if delay is not None:
            payload["delay"] = bool(delay)
        if end_time is not None:
            payload["endTime"] = end_time
        if num is not None:
            payload["num"] = num
        if right is not None:
            payload["right"] = right
        if start_time is not None:
            payload["startTime"] = start_time
        if suspension is not None:
            payload["suspension"] = suspension
        if time is not None:
            payload["time"] = time
        return self.client.post("/api/v1/market/kline", data=payload)

    def min(self, code, count=5):
        """分时数据
        """
        params = {"code": code}
        if count is not None:
            params["count"] = count
        return self.client.get("/api/v1/market/min", params=params)

    def orderbook(self, code, count=5):
        """盘口/买卖档
        """
        params = {"code": code}
        if count is not None:
            params["count"] = count
        return self.client.get("/api/v1/market/secu/orderbook", params=params)

    def tick(self, code, count=20, id=-1, ts=None):
        """逐笔成交
        """
        params = {"code": code, "count": count, "id": id}
        if ts is not None:
            params["ts"] = ts
        return self.client.get("/api/v1/market/secu/tick", params=params)

    def broker_list(self, code):
        """买卖盘经纪商队列
        """
        return self.client.get(
            "/api/v1/market/secu/brokerq",
            params={"code": code},
        )