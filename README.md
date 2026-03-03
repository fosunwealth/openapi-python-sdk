# Fosun Wealth OpenAPI Python SDK

复星财富 OpenAPI 的 Python 客户端封装，支持会话鉴权（ECDH）、请求签名与响应解密，提供账户、交易、组合、行情等接口。

## 环境要求

- Python 3.8+
- 依赖：`requests`、`cryptography`

## 安装

### 从源码安装

如果希望集成到您的业务代码中，也可以将 `openapi-python-sdk` 目录复制到您的业务项目，并在您的业务代码根目录下执行同样的安装命令：

```bash
pip install -e ./openapi-python-sdk
```

将自动安装依赖 `requests`、`cryptography`。若需固定版本，可使用：

```
requests>=2.28.0
cryptography>=41.0.0
```

**注意**：SDK 通过环境变量获取密钥内容。如果未检测到密钥，将直接抛出异常并停止运行。  
请在启动前配置以下环境变量（例如在 `.env` 文件或操作系统环境中设置）：

- `FSOPENAPI_SERVER_PUBLIC_KEY`:  设置为您的公钥内容（PEM 格式，单行/多行均可）  
- `FSOPENAPI_CLIENT_PRIVATE_KEY`: 设置为您的私钥内容（PEM 格式，单行/多行均可）  

例如（Linux/macOS bash）：

```bash
export FSOPENAPI_CLIENT_PUBLIC_KEY="$(cat ./public.pem)"
export FSOPENAPI_CLIENT_PRIVATE_KEY="$(cat ./private.pem)"
```

如果密钥未通过环境变量正确提供，SDK 初始化会抛出错误并提示密钥缺失。

## 快速开始


```python
from fsopenapi import SDKClient
from fsopenapi import APIError, AuthenticationError

BASE_URL = "https://your-gateway-host/api/v1"  # 网关 base_url，不含末尾 /
API_KEY = "your-api-key"

client = SDKClient(BASE_URL, API_KEY)

# 会话由 SDK 自动管理（ECDH 握手、续期），首次调用业务接口时会自动建连
# 查询账户列表
accounts = client.account.list_accounts()
print(accounts)

# 查询持仓（可选 sub_account_id、分页等）
holdings = client.portfolio.get_holdings(sub_account_id="your-sub-account-id", start=0, count=20)
print(holdings)

# 行情（不加密）
quote = client.market.quote(codes=["hk00700", "usAAPL"])
print(quote)
```

## 模块说明

| 模块 | 说明 |
|------|------|
| `client.session` | 会话管理：创建/查询/删除会话、本地会话状态 |
| `client.account` | 账户：交易账户列表 |
| `client.portfolio` | 组合：资金汇总、持仓 |
| `client.trade` | 交易：下单、撤单、订单列表、资金流水、买卖信息 |
| `client.market` | 行情：报价、K 线、分时、盘口、逐笔、经纪队列 |

## 使用示例

### 1. 会话管理

```python
# 创建会话（通常由 SDK 内部自动调用）
session_info = client.session.create_session()
print(session_info)  # sessionId, serverPublicKey, expiresIn, expiresAt

# 查询服务端当前会话
current = client.session.query_session()
print(current)

# 检查本地会话是否有效
if client.session.is_session_valid():
    print("会话有效")

# 主动登出
client.session.delete_session()
```

### 2. 账户

```python
# 账户列表（空 body）
accounts = client.account.list_accounts()
```

### 3. 组合

```python
# 资金汇总（可按 sub_account_id、client_id、currency 筛选）
summary = client.portfolio.get_assets_summary(sub_account_id="sub-xxx")

# 持仓列表（分页、产品类型、币种、标的等）
holdings = client.portfolio.get_holdings(
    sub_account_id="sub-xxx",
    start=0,
    count=100,
    product_types=[1, 2],
    currencies=["HKD", "USD"],
)
```

### 4. 交易

```python
# 下单（限价单示例）
order = client.trade.create_order(
    sub_account_id="sub-xxx",
    stock_code="00700",
    direction=1,       # 1 买 2 卖
    order_type=1,     # 限价
    quantity="100",
    price="350.00",
    market_code="hk",
    currency="HKD",
)
print(order)

# 撤单
client.trade.cancel_order(order_id="order-xxx", sub_account_id="sub-xxx")

# 订单列表（分页、状态、日期、方向等）
orders = client.trade.list_orders(
    sub_account_id="sub-xxx",
    start=0,
    count=20,
    status_arr=[20, 40],
    from_date="2025-01-01",
    to_date="2025-01-31",
)

# 资金流水
flows = client.trade.get_cash_flows(
    sub_account_id="sub-xxx",
    trade_date_from="2025-01-01",
    trade_date_to="2025-01-31",
)

# 买卖信息（下单前校验）
bid_ask = client.trade.get_bid_ask_info(
    sub_account_id="sub-xxx",
    stock_code="00700",
    order_type=3,
    market_code="hk",
    quantity="100",
    direction=1,
)
```

### 5. 行情

```python
# 批量报价（codes 为 marketCode+stockCode，如 hk00700、usAAPL）
quote = client.market.quote(codes=["hk00700", "usAAPL"], delay=False)

# K 线（code 格式: marketCode + stockCode，如 hk00700）
klines = client.market.kline("hk00700", ktype="day", num=30)

# 分时
min_data = client.market.min("hk00700", count=5)

# 盘口/买卖档
orderbook = client.market.orderbook("hk00700", count=5)

# 逐笔成交
ticks = client.market.tick("hk00700", count=20, id=-1)

# 买卖盘经纪商队列
brokers = client.market.broker_list("hk00700")
```

## 异常处理

```python
from openapi_client import APIError, AuthenticationError, PermissionError, CacheError

try:
    data = client.account.list_accounts()
except AuthenticationError as e:
    print(f"鉴权失败: {e.code} - {e.message}")
except PermissionError as e:
    print(f"权限错误: {e.code} - {e.message}")
except APIError as e:
    print(f"接口错误: {e.code} - {e.message} (requestId: {e.request_id})")
```

## 注意事项

1. **base_url**：填写网关完整 base_url（如 `https://host/api/v1`），不要以 `/` 结尾。
2. **API Key**：由开放平台下发，请勿泄露。
3. **会话**：SDK 会自动完成 ECDH 建连与过期前续期，业务侧一般无需手动调用 `session.create_session()`。
4. **行情接口**：走 `/market/`，仅签名不加密；交易/账户等接口请求体与响应支持 AES-GCM 加解密。
