from .prefix import ensure_ops_api_prefix


def _require_apply_account_id(apply_account_id):
    if apply_account_id is None or not str(apply_account_id).strip():
        raise ValueError("apply_account_id is required for OPS portfolio APIs")
    return str(apply_account_id).strip()


class OpsPortfolioAPI:
    def __init__(self, client):
        self.client = client

    def get_assets_summary(self, sub_account_id, apply_account_id, client_id=None, currency=None):
        """查询资金汇总"""
        ensure_ops_api_prefix(self.client)
        payload = {
            "subAccountId": str(sub_account_id),
            "applyAccountId": _require_apply_account_id(apply_account_id),
        }
        if client_id is not None:
            payload["clientId"] = int(client_id)
        if currency is not None:
            payload["currency"] = str(currency)
        return self.client.post("/v1/portfolio/CashSummary", data=payload)

    def get_holdings(
        self,
        sub_account_id,
        apply_account_id,
        start=0,
        count=100,
        product_types=None,
        currencies=None,
        symbols=None,
        use_us_pre=False,
        use_us_post=False,
        use_us_night=False,
        client_id=None,
        sub_account_class=None,
    ):
        """查询持仓"""
        ensure_ops_api_prefix(self.client)
        _pt = product_types if isinstance(product_types, list) else ([product_types] if product_types else [])
        _cc = currencies if isinstance(currencies, list) else ([currencies] if currencies else [])
        _sym = symbols if isinstance(symbols, list) else ([symbols] if symbols else [])
        payload = {
            "subAccountId": str(sub_account_id),
            "applyAccountId": _require_apply_account_id(apply_account_id),
            "start": int(start),
            "count": int(count),
            "useUsPre": bool(use_us_pre),
            "useUsPost": bool(use_us_post),
            "useUsNight": bool(use_us_night),
            "productTypes": [int(x) for x in _pt],
            "currencies": [str(x) for x in _cc],
            "symbols": [str(x) for x in _sym],
        }
        if client_id is not None:
            payload["clientId"] = int(client_id)
        if sub_account_class is not None:
            payload["subAccountClass"] = int(sub_account_class)
        return self.client.post("/v1/portfolio/Holdings", data=payload)
