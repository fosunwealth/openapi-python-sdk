# RWA 票据行情 API（对接 market 服务 /api/v1/market/rwa/*）

_DEFAULT_PAGE_START = 0
_DEFAULT_PAGE_COUNT = 20


def _require_non_empty_symbol(symbol):
    """校验 symbol 非空（与 Go 侧 TrimSpace 后非空一致）。"""
    if symbol is None:
        raise ValueError("symbol 为必填")
    s = str(symbol).strip()
    if not s:
        raise ValueError("symbol 不能为空")
    return s


class RwaAPI:
    def __init__(self, client):
        self.client = client

    def note_list(
        self,
        currency=None,
        start=None,
        count=None,
    ):
        """RWA 票据货架列表，对应 POST /v1/market/rwa/list。

        请求体仅包含以下字段（camelCase 由本方法组装）：
            currency、start、count。

        参数说明：
            currency (str|None): 币种；None 时按空字符串传。示例：'USD'。
            start (int|None): 分页起始；未传或 None 时使用默认 0。示例：0。
            count (int|None): 每页条数；未传或 None 时使用默认 20。示例：20。

        调用示例：
            client.rwa.note_list(currency='USD', start=0, count=20)
        """
        eff_start = _DEFAULT_PAGE_START if start is None else int(start)
        eff_count = _DEFAULT_PAGE_COUNT if count is None else int(count)
        payload = {
            "currency": "" if currency is None else str(currency),
            "start": eff_start,
            "count": eff_count,
        }
        return self.client.post("/v1/market/rwa/list", data=payload)

    def note_detail(self, symbol):
        """RWA 票据详情，对应 POST /v1/market/rwa/detail。

        参数说明：
            symbol (str): 票据标识，必填。示例：'RWA-DEMO-01'。

        调用示例：
            client.rwa.note_detail('RWA-DEMO-01')
        """
        sym = _require_non_empty_symbol(symbol)
        payload = {"symbol": sym}
        return self.client.post("/v1/market/rwa/detail", data=payload)
