class PortfolioAPI:
    def __init__(self, client):
        self.client = client

    def get_assets_summary(self, sub_account_id=None, client_id=None, currency=None):
        """查询账户资金汇总"""
        payload = {}
        if sub_account_id is not None:
            payload["subAccountId"] = str(sub_account_id)
        if client_id is not None:
            payload["clientId"] = int(client_id)
        if currency is not None:
            payload["currency"] = str(currency)
        return self.client.post("/api/v1/portfolio/CashSummary", data=payload)

    def get_holdings(self, sub_account_id=None, start=0, count=100, product_types=None, currencies=None, symbols=None, use_us_pre=False, use_us_post=False, use_us_night=False, client_id=None):
        _pt = product_types if isinstance(product_types, list) else ([product_types] if product_types else [])
        _cc = currencies if isinstance(currencies, list) else ([currencies] if currencies else [])
        _sym = symbols if isinstance(symbols, list) else ([symbols] if symbols else [])
        payload = {
            "start": int(start),
            "count": int(count),
            "useUsPre": bool(use_us_pre),
            "useUsPost": bool(use_us_post),
            "useUsNight": bool(use_us_night),
            "productTypes": [int(x) for x in _pt],
            "currencies": [str(x) for x in _cc],
            "symbols": [str(x) for x in _sym],
        }
        if sub_account_id is not None:
            payload["subAccountId"] = str(sub_account_id)
        if client_id is not None:
            payload["clientId"] = int(client_id)
        return self.client.post("/api/v1/portfolio/Holdings", data=payload)
