import os
from .client import OpenAPIClient
from .api.trade import TradeAPI
from .api.portfolio import PortfolioAPI
from .api.account import AccountAPI
from .api.market import MarketAPI
from .api.session import SessionAPI
from .exceptions import APIError, AuthenticationError, PermissionError, CacheError


class SDKClient(OpenAPIClient):
    def __init__(self, base_url, api_key):
        missing = [k for k in ("FSOPENAPI_SERVER_PUBLIC_KEY", "FSOPENAPI_CLIENT_PRIVATE_KEY") if not os.environ.get(k)]
        if missing:
            raise ValueError(f"缺少必要的环境变量: {', '.join(missing)}。请在启动前设置 FSOPENAPI_SERVER_PUBLIC_KEY 和 FSOPENAPI_CLIENT_PRIVATE_KEY")
        super().__init__(base_url, api_key)
        self.session = SessionAPI(self)
        self.trade = TradeAPI(self)
        self.portfolio = PortfolioAPI(self)
        self.account = AccountAPI(self)
        self.market = MarketAPI(self)


__all__ = [
    "SDKClient",
    "APIError",
    "AuthenticationError",
    "PermissionError",
    "CacheError",
    "SessionAPI",
    "TradeAPI",
    "PortfolioAPI",
    "AccountAPI",
    "MarketAPI",
]
