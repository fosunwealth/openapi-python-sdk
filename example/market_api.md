# 证券行情接口文档（Market API）

本文档描述 OpenAPI Python SDK 中 `client.market` 的六个接口，包含 SDK 调用方式、请求参数与响应格式。

**前置条件**：需先创建会话并完成鉴权，详见 `market_example.py` 中的 `ensure_session()`。

---

## 六个接口 SDK 调用速览

| 接口 | SDK 方法 | 入参形式 | market_example.py 调用 |
|------|----------|----------|------------------------|
| 1. 批量报价 | `client.market.quote(codes, fields=?)` | `codes` 必填（list），`fields` 可选 | `--api quote`，可选 `--quote-fields` |
| 2. K 线 | `client.market.kline(code, ktype, num=?, ...)` | `code`、`ktype` 必填，其余可选 | `--api kline`，可选 `--kline-ktype` `--kline-num` 等 |
| 3. 分时 | `client.market.min(code, count=5)` | `code` 必填，`count` 可选 | `--api min`，可选 `--min-count` |
| 4. 盘口 | `client.market.orderbook(code, count=5)` | `code` 必填，`count` 可选 | `--api orderbook`，可选 `--orderbook-count` |
| 5. 逐笔成交 | `client.market.tick(code, count=20, id=-1, ts=?)` | `code` 必填，其余可选 | `--api tick`，可选 `--tick-count` `--tick-id` `--tick-ts` |
| 6. 经纪商队列 | `client.market.broker_list(code)` | `code` 必填 | `--api broker_list` |

---

## 1. 批量报价 quote

批量获取证券报价。

| 项目 | 说明 |
|------|------|
| **HTTP** | POST |
| **路径** | `/api/v1/market/secu/quote` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| codes | string[] | 是 | 证券代码列表 |
| fields | string[] | 否 | 指定返回字段 |

### SDK 调用

**方法签名**：`quote(codes, fields=None)`

**调用示例**：

```python
# 单个代码
r = client.market.quote(codes=["hk00700"])

# 多个代码
r = client.market.quote(codes=["hk00700", "hk09988"])

# 指定返回字段
r = client.market.quote(
    codes=["hk00700"],
    fields=["last", "bid", "ask", "volume"]
)
```

**命令行调用**：

```bash
# 基础调用
python market_example.py --api quote --market-code hk00700

# 带可选参数
python market_example.py --api quote --market-code hk00700 --quote-fields price chgVal
```

### 请求示例

```json
{
  "codes": ["hk00700"]
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "hk00700": {
      "last": 350.0,
      "bid": 349.8,
      "ask": 350.2,
      "volume": 1000000,
      "open": 348.0,
      "high": 352.0,
      "low": 347.5,
      "close": 350.0
    }
  }
}
```

---

## 2. K 线 kline

获取证券 K 线数据。

| 项目 | 说明 |
|------|------|
| **HTTP** | POST |
| **路径** | `/api/v1/market/kline` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 证券代码 |
| ktype | string | 是 | K 线类型：`1`、`5`、`15`、`day` 等 |
| num | int | 否 | 返回条数 |
| time | int64 | 否 | 时间戳 |
| startTime | int64 | 否 | 开始时间戳 |
| endTime | int64 | 否 | 结束时间戳 |
| right | string | 否 | 复权方式 |
| delay | bool | 否 | 是否延迟行情 |
| suspension | int | 否 | 停牌处理 |

### SDK 调用

**方法签名**：`kline(code, ktype, delay=None, end_time=None, num=None, right=None, start_time=None, suspension=None, time=None)`

**调用示例**：

```python
# 仅必填参数
r = client.market.kline("hk00700", "day")

# 指定条数
r = client.market.kline("hk00700", ktype="day", num=5)

# 含时间范围
r = client.market.kline(
    code="hk00700",
    ktype="day",
    start_time=1699000000000,
    end_time=1699086400000
)
```

**命令行调用**：

```bash
# 基础调用（默认 ktype=day）
python market_example.py --api kline --market-code hk00700

# 带可选参数
python market_example.py --api kline --market-code hk00700 --kline-ktype day --kline-num 10
python market_example.py --api kline --market-code hk00700 --kline-start-time 1699000000000 --kline-end-time 1699086400000
```

### 请求示例

```json
{
  "code": "hk00700",
  "ktype": "day",
  "num": 5
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "code": "hk00700",
    "ktype": "day",
    "data": [
      [1699000000000, 348.0, 352.0, 347.5, 350.0, 1000000],
      [1699086400000, 350.0, 355.0, 349.0, 353.0, 1200000]
    ]
  }
}
```

---

## 3. 分时 min

获取证券分时数据。

| 项目 | 说明 |
|------|------|
| **HTTP** | GET |
| **路径** | `/api/v1/market/min` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 证券代码 |
| count | int | 否 | 返回点数，默认 5 |

### SDK 调用

**方法签名**：`min(code, count=5)`

**调用示例**：

```python
# 使用默认 count
r = client.market.min("hk00700")

# 指定 count
r = client.market.min("hk00700", count=5)
```

**命令行调用**：

```bash
# 基础调用（默认 count=5）
python market_example.py --api min --market-code hk00700

# 指定返回点数
python market_example.py --api min --market-code hk00700 --min-count 10
```

### 请求示例

```
GET /api/v1/market/min?code=hk00700&count=5
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "code": "hk00700",
    "points": [
      [540, 348.5],
      [541, 349.0],
      [542, 349.2],
      [543, 349.5],
      [544, 350.0]
    ]
  }
}
```

---

## 4. 盘口 orderbook

获取证券买卖档盘口数据。

| 项目 | 说明 |
|------|------|
| **HTTP** | GET |
| **路径** | `/api/v1/market/secu/orderbook` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 证券代码 |
| count | int | 否 | 档位数量，默认 5 |

### SDK 调用

**方法签名**：`orderbook(code, count=5)`

**调用示例**：

```python
# 使用默认 count
r = client.market.orderbook("hk00700")

```

**命令行调用**：

```bash
# 基础调用（默认 count=5）
python market_example.py --api orderbook --market-code hk00700

# 指定档位数量
python market_example.py --api orderbook --market-code hk00700 --orderbook-count 10
```

### 请求示例

```
GET /api/v1/market/secu/orderbook?code=hk00700&count=10
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "code": "hk00700",
    "bid": [
      [349.8, 1000],
      [349.6, 2000],
      [349.4, 1500],
      [349.2, 3000],
      [349.0, 2500]
    ],
    "ask": [
      [350.0, 800],
      [350.2, 1200],
      [350.4, 1800],
      [350.6, 2200],
      [350.8, 1500]
    ]
  }
}
```

---

## 5. 逐笔成交 tick

获取证券逐笔成交数据。

| 项目 | 说明 |
|------|------|
| **HTTP** | GET |
| **路径** | `/api/v1/market/secu/tick` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 证券代码 |
| count | int | 否 | 返回条数，默认 20 |
| id | int | 否 | 起始 tick id，-1 表示最新 |
| ts | int64 | 否 | 时间戳 |

### SDK 调用

**方法签名**：`tick(code, count=20, id=-1, ts=None)`

**调用示例**：

```python
# 仅必填参数（使用默认 count=20, id=-1）
r = client.market.tick("hk00700")

# 关键字传参
r = client.market.tick("hk00700", count=10, id=-1)

# 从指定 id 向前拉取
r = client.market.tick(code="hk00700", count=50, id=12345)
```

**命令行调用**：

```bash
# 基础调用（默认 count=20, id=-1）
python market_example.py --api tick --market-code hk00700

# 带可选参数
python market_example.py --api tick --market-code hk00700 --tick-count 50 --tick-id -1
```

### 请求示例

```
GET /api/v1/market/secu/tick?code=hk00700&count=10&id=-1
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "code": "hk00700",
    "ticks": [
      {
        "id": 12345,
        "time": 1699000000000,
        "price": 350.0,
        "volume": 100,
        "side": "B"
      },
      {
        "id": 12346,
        "time": 1699000001000,
        "price": 350.2,
        "volume": 50,
        "side": "S"
      }
    ]
  }
}
```

---

## 6. 经纪商队列 broker_list

获取买卖盘经纪商队列。

| 项目 | 说明 |
|------|------|
| **HTTP** | GET |
| **路径** | `/api/v1/market/secu/brokerq` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 证券代码 |

### SDK 调用

**方法签名**：`broker_list(code)`

**调用示例**：

```python
r = client.market.broker_list("hk00700")
```

**命令行调用**：

```bash
python market_example.py --api broker_list --market-code hk00700
```

### 请求示例

```
GET /api/v1/market/secu/brokerq?code=hk00700
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "code": "hk00700",
    "bidBrokers": [
      {"brokerId": "B001", "brokerName": "经纪商A", "volume": 500},
      {"brokerId": "B002", "brokerName": "经纪商B", "volume": 300}
    ],
    "askBrokers": [
      {"brokerId": "A001", "brokerName": "经纪商C", "volume": 400},
      {"brokerId": "A002", "brokerName": "经纪商D", "volume": 250}
    ]
  }
}
```

---

## 统一错误响应

接口失败时返回：

```json
{
  "code": 70001,
  "message": "Invalid parameters",
  "requestId": "req-xxx",
  "data": null
}
```

| 错误码 | 说明 |
|--------|------|
| 70001 | 参数错误 |
| 70002 | 下游服务错误 |
| 70003 | 权限错误 |

---

## 使用 market_example.py 验证

通过 `--api` 指定要调用的接口，支持单独或组合调用。六个接口的可选参数均支持通过命令行传入（不传则使用默认值）：

| 接口 | 可选参数 |
|------|----------|
| quote | `--quote-fields` |
| kline | `--kline-ktype`, `--kline-num`, `--kline-delay`, `--kline-time`, `--kline-start-time`, `--kline-end-time`, `--kline-right`, `--kline-suspension` |
| min | `--min-count` |
| orderbook | `--orderbook-count` |
| tick | `--tick-count`, `--tick-id`, `--tick-ts` |
| broker_list | 无 |

```bash
# 单独调用某个接口
python market_example.py --api quote --market-code hk00700
python market_example.py --api kline --market-code hk00700
python market_example.py --api min --market-code hk00700
python market_example.py --api orderbook --market-code hk00700
python market_example.py --api tick --market-code hk00700
python market_example.py --api broker_list --market-code hk00700

# 带可选参数调用
python market_example.py --api quote --market-code hk00700 --quote-fields last bid ask
python market_example.py --api kline --market-code hk00700 --kline-ktype 5 --kline-num 10
python market_example.py --api tick --market-code hk00700 --tick-count 50 --tick-id -1

# 组合调用多个接口（逗号分隔）
python market_example.py --api kline,quote,tick --market-code hk00700

# 调用全部 6 个证券行情接口
python market_example.py --api all --market-code hk00700

# 使用默认证券代码 hk00700
python market_example.py --api all
```

---

## 快速集成示例

```python
from fsopenapi import SDKClient, APIError, AuthenticationError, PermissionError
import json
import os

BASE_URL = os.environ.get("FSOPENAPI_BASE_URL", "https://openapi-sit.fosunxcz.com")
API_KEY = os.environ.get("FSOPENAPI_API_KEY", "your-api-key")

client = SDKClient(BASE_URL, API_KEY)

# 1. 创建会话（首次调用需执行）
client.session.create_session()

# 2. 调用六个行情接口
market_code = "hk00700"

# 批量报价
quote = client.market.quote(codes=[market_code])

# K 线
kline = client.market.kline(market_code, ktype="day", num=5)

# 分时
min_data = client.market.min(market_code, count=5)

# 盘口
orderbook = client.market.orderbook(market_code, count=5)

# 逐笔成交
tick = client.market.tick(market_code, count=10, id=-1)

# 经纪商队列
broker_list = client.market.broker_list(market_code)

print(json.dumps(quote, ensure_ascii=False, indent=2))
```
