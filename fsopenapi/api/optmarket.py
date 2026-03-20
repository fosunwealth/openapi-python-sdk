# 期权行情 API

class OptMarketAPI:
    def __init__(self, client):
        self.client = client

    def orderbook(self, code):
        """期权盘口/买卖档
        """
        return self.client.get(
            "/v1/market/opt/secu/orderbook",
            params={"code": code},
        )

    def kline(
        self,
        code,
        ktype,
        end_time=None,
        interval=None,
        num=None,
        start_time=None,
        suspension=None,
        time=None,
    ):
        """期权 K 线
        """
        payload = {"code": code, "ktype": ktype}
        if end_time is not None:
            payload["endTime"] = end_time
        if interval is not None:
            payload["interval"] = interval
        if num is not None:
            payload["num"] = num
        if start_time is not None:
            payload["startTime"] = start_time
        if suspension is not None:
            payload["suspension"] = suspension
        if time is not None:
            payload["time"] = time
        return self.client.post("/v1/market/opt/kline", data=payload)

    def quote(self, codes, fields=None):
        """期权批量证券报价（最多 300 个）
        """
        payload = {"codes": list(codes)}
        if fields is not None:
            payload["fields"] = list(fields)
        return self.client.post("/v1/market/opt/secu/quote", data=payload)

    def tick(self, code, count=20, id=-1):
        """期权逐笔成交
        """
        params = {"code": code, "count": count, "id": id}
        return self.client.get("/v1/market/opt/tick", params=params)

    def day_min(self, code, num=5):
        """期权多日分时（1~10 天）
        """
        params = {"code": code}
        if num is not None:
            params["num"] = num
        return self.client.get("/v1/market/opt/day_min", params=params)
