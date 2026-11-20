from .client import OpenAPIClient
from .api.trade import TradeAPI
from .api.portfolio import PortfolioAPI
from .api.account import AccountAPI
from .api.ops import OpsTradeAPI, OpsPortfolioAPI, OpsAccountAPI
from .api.market import MarketAPI
from .api.market_push import MarketPushAPI
from .api.optmarket import OptMarketAPI
from .api.rwa import RwaAPI
from .api.session import SessionAPI
from .api.wealth import WealthAPI
from .exceptions import APIError, AuthenticationError, PermissionError, CacheError
from .key_loader import missing_identity_key_configs
from .lang import DEFAULT_LANG, LANG_EN, LANG_ZH_CN, LANG_ZH_TC
from .logging_utils import JsonFormatter, get_sdk_logger
from .session_store import migrate_session_snapshot, read_session_snapshot, write_session_snapshot


class SDKClient(OpenAPIClient):
    def __init__(self, base_url=None, api_key=None, logger=None, logging_enable=False, log_body=False, ssl_verify=None, request_timeout=(5, 30)):
        missing = missing_identity_key_configs()
        if missing:
            raise ValueError(
                "缺少必要的密钥配置: "
                + "；".join(missing)
                + "。请设置环境变量，或改用 *_PATH 指向密钥文件"
            )
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            logger=logger,
            logging_enable=logging_enable,
            log_body=log_body,
            ssl_verify=ssl_verify,
            request_timeout=request_timeout,
        )
        self.session = SessionAPI(self)
        self.trade = TradeAPI(self)
        self.portfolio = PortfolioAPI(self)
        self.account = AccountAPI(self)
        self.opsTrade = OpsTradeAPI(self)
        self.opsPortfolio = OpsPortfolioAPI(self)
        self.opsAccount = OpsAccountAPI(self)
        self.market = MarketAPI(self)
        self.market_push = MarketPushAPI(self)
        self.optmarket = OptMarketAPI(self)
        self.rwa = RwaAPI(self)
        self.wealth = WealthAPI(self)


__all__ = [
    "SDKClient",
    "DEFAULT_LANG",
    "LANG_EN",
    "LANG_ZH_CN",
    "LANG_ZH_TC",
    "APIError",
    "AuthenticationError",
    "PermissionError",
    "CacheError",
    "JsonFormatter",
    "SessionAPI",
    "TradeAPI",
    "PortfolioAPI",
    "AccountAPI",
    "OpsTradeAPI",
    "OpsPortfolioAPI",
    "OpsAccountAPI",
    "MarketAPI",
    "MarketPushAPI",
    "OptMarketAPI",
    "RwaAPI",
    "WealthAPI",
    "get_sdk_logger",
    "write_session_snapshot",
    "read_session_snapshot",
    "migrate_session_snapshot",
]
