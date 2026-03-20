import os

from .client import OpenAPIClient
from .api.trade import TradeAPI
from .api.portfolio import PortfolioAPI
from .api.account import AccountAPI
from .api.market import MarketAPI
from .api.market_push import MarketPushAPI
from .api.optmarket import OptMarketAPI
from .api.session import SessionAPI
from .exceptions import APIError, AuthenticationError, PermissionError, CacheError
from .logging_utils import JsonFormatter, get_sdk_logger


class SDKClient(OpenAPIClient):
    def __init__(self, base_url=None, api_key=None, logger=None, logging_enable=False, log_body=False):
        missing = [k for k in ("FSOPENAPI_SERVER_PUBLIC_KEY", "FSOPENAPI_CLIENT_PRIVATE_KEY") if not os.environ.get(k)]
        if missing:
            raise ValueError(f"缺少必要的环境变量: {', '.join(missing)}。请在启动前设置 FSOPENAPI_SERVER_PUBLIC_KEY 和 FSOPENAPI_CLIENT_PRIVATE_KEY")
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            logger=logger,
            logging_enable=logging_enable,
            log_body=log_body,
        )
        self.session = SessionAPI(self)
        self.trade = TradeAPI(self)
        self.portfolio = PortfolioAPI(self)
        self.account = AccountAPI(self)
        self.market = MarketAPI(self)
        self.market_push = MarketPushAPI(self)
        self.optmarket = OptMarketAPI(self)


__all__ = [
    "SDKClient",
    "APIError",
    "AuthenticationError",
    "PermissionError",
    "CacheError",
    "JsonFormatter",
    "SessionAPI",
    "TradeAPI",
    "PortfolioAPI",
    "AccountAPI",
    "MarketAPI",
    "MarketPushAPI",
    "OptMarketAPI",
    "get_sdk_logger",
]
