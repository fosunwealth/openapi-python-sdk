# 期权行情接口文档（OptMarket API）

本文档描述 OpenAPI Python SDK 中 `client.optmarket` 的五个接口，包含请求参数与响应格式。

**前置条件**：需先创建会话并完成鉴权，详见 `option_example.py` 中的 `ensure_session()`。

### 五个接口 SDK 调用速览

| 接口 | SDK 方法 | 入参形式 | option_example.py 单独调用 |
|------|----------|----------|---------------------------|
| 1. 盘口 | `client.optmarket.orderbook(code)` | `code` 必填 | `--opt-api orderbook` |
| 2. K 线 | `client.optmarket.kline(code, ktype, num=?, ...)` | `code`、`ktype` 必填，其余可选 | `--opt-api kline`，可选 `--kline-*` |
| 3. 批量报价 | `client.optmarket.quote(codes, fields=?)` | `codes` 必填（list），`fields` 可选 | `--opt-api quote`，可选 `--quote-fields` |
| 4. 逐笔成交 | `client.optmarket.tick(code, count=20, id=-1)` | `code` 必填，`count`、`id` 可选 | `--opt-api tick`，可选 `--tick-count` `--tick-id` |
| 5. 多日分时 | `client.optmarket.day_min(code, num=5)` | `code` 必填，`num` 可选 | `--opt-api day_min`，可选 `--day-min-num` |

---

## 1. 期权盘口 orderbook

获取期权买卖档盘口数据。

| 项目 | 说明 |
|------|------|
| **HTTP** | GET |
| **路径** | `/api/v1/optmarket/secu/orderbook` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 期权代码，如 `usAAPL 20260320 270.0 CALL` |

### SDK 调用

**方法签名**：`orderbook(code)`

**入参形式**：

| 参数 | 传入方式 | 说明 |
|------|----------|------|
| code | 位置参数或关键字 | 必填，字符串 |

**调用示例**：

```python
# 关键字传参
r = client.optmarket.orderbook(code="usAAPL 20260320 270.0 CALL")

# 位置传参
r = client.optmarket.orderbook("usAAPL 20260320 270.0 CALL")
```

**option_example.py 调用命令**（仅调用 orderbook）：

```bash
python option_example.py --opt-api orderbook --opt-code "usAAPL 20260320 270.0 CALL"
```

### 响应格式

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "code": "usAAPL 20260320 270.0 CALL",
    "bid": [...],
    "ask": [...]
  }
}
```

---

## 2. 期权 K 线 kline

获取期权 K 线数据。

| 项目 | 说明 |
|------|------|
| **HTTP** | POST |
| **路径** | `/api/v1/optmarket/kline` |

### 请求参数

| 参数         | 类型 | 必填 | 说明                                   |
|------------|------|------|--------------------------------------|
| code       | string | 是 | 期权代码                                 |
| ktype      | string | 是 | K 线类型：`day` 、`min1`、`min5`、`min15` 等 |
| num        | int | 否 | 返回条数，默认 100                          |
| time       | int64 | 否 | 时间戳                                  |
| startTime  | int64 | 否 | 开始时间戳                                |
| endTime    | int64 | 否 | 结束时间戳                                |
| interval   | int | 否 | 间隔                                   |
| suspension | int | 否 | 停牌处理                                 |

### SDK 调用

**方法签名**：`kline(code, ktype, end_time=None, interval=None, num=None, start_time=None, suspension=None, time=None)`

**入参形式**：

| 参数 | 传入方式 | 必填 | 默认值 | 说明 |
|------|----------|------|--------|------|
| code | 位置/关键字 | 是 | - | 期权代码 |
| ktype | 位置/关键字 | 是 | - | K 线类型 |
| end_time | 关键字 | 否 | None | 结束时间戳 |
| interval | 关键字 | 否 | None | 间隔 |
| num | 关键字 | 否 | None | 返回条数 |
| start_time | 关键字 | 否 | None | 开始时间戳 |
| suspension | 关键字 | 否 | None | 停牌处理 |
| time | 关键字 | 否 | None | 时间戳 |

**调用示例**：

```python
# 仅必填参数
r = client.optmarket.kline("usAAPL 20260320 270.0 CALL", "day")

# 关键字传参，含可选参数
r = client.optmarket.kline(
    code="usAAPL 20260320 270.0 CALL",
    ktype="day",
    num=5
)

# 含时间范围
r = client.optmarket.kline(
    code="usAAPL 20260320 270.0 CALL",
    ktype="day",
    start_time=1699000000000,
    end_time=1699086400000
)
```

**option_example.py 调用命令**（仅调用 kline）：

```bash
# 基础调用
python option_example.py --opt-api kline --opt-code "usAAPL 20260320 270.0 CALL" --kline-ktype day/min1/min5 --kline-num 10

# 含时间范围
python option_example.py --opt-api kline --opt-code "usAAPL 20260320 270.0 CALL" --kline-ktype day/min1/min5 --kline-start-time xxx --kline-end-time xxx

# 含可选参数
python option_example.py --opt-api kline --opt-code "usAAPL 20260320 270.0 CALL" --kline-ktype day/min1/min5 --kline-num 20 --kline-time 1699000000000 --kline-interval xx --kline-suspension xx
```

### 响应格式

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "code": "usAAPL 20260320 270.0 CALL",
    "ktype": "1",
    "data": [
      [1699000000000, 1.5, 1.6, 1.4, 1.55, 1000]
    ]
  }
}
```

---

## 3. 期权批量报价 quote

批量获取期权报价，最多 300 个。

| 项目 | 说明 |
|------|------|
| **HTTP** | POST |
| **路径** | `/api/v1/optmarket/secu/quote` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| codes | string[] | 是 | 期权代码列表，最多 300 个 |
| fields | string[] | 否 | 指定返回字段 |

### SDK 调用

**方法签名**：`quote(codes, fields=None)`

**入参形式**：

| 参数 | 传入方式 | 必填 | 默认值 | 说明 |
|------|----------|------|--------|------|
| codes | 位置/关键字 | 是 | - | 期权代码列表，list 或可迭代对象 |
| fields | 关键字 | 否 | None | 指定返回字段列表 |

**调用示例**：

```python
# 单个代码（列表形式）
r = client.optmarket.quote(codes=["usAAPL 20260320 270.0 CALL"])

# 多个代码
r = client.optmarket.quote(codes=[
    "usAAPL 20260320 270.0 CALL",
    "usAAPL 20260320 280.0 CALL"
])

# 指定返回字段
r = client.optmarket.quote(
    codes=["usAAPL 20260320 270.0 CALL"],
    fields=["iv", "hv"]
)
```

**option_example.py 调用命令**（仅调用 quote）：

```bash
# 单代码（使用 opt-code）
python option_example.py --opt-api quote --opt-code "usAAPL 20260320 270.0 CALL"

# 多代码（使用 quote-codes，逗号分隔）
python option_example.py --opt-api quote --quote-codes "usAAPL 20260320 270.0 CALL,usAAPL 20260320 280.0 CALL"

# 指定返回字段（使用 quote-fields，逗号分隔）
python option_example.py --opt-api quote --opt-code "usAAPL 20260320 270.0 CALL" --quote-fields iv,hv

```

### 响应格式

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "usAAPL 20260320 270.0 CALL": {
      "last": 1.5,
      "bid": 1.48,
      "ask": 1.52,
      "volume": 1000
    },
    "usAAPL 20260320 280.0 CALL": { ... }
  }
}
```

---

## 4. 期权逐笔成交 tick

获取期权逐笔成交数据。

| 项目 | 说明 |
|------|------|
| **HTTP** | GET |
| **路径** | `/api/v1/optmarket/tick` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 期权代码 |
| count | int | 否 | 返回条数，-500~500，默认 20 |
| id | int | 否 | 起始 tick id，-1 表示最新 |

### SDK 调用

**方法签名**：`tick(code, count=20, id=-1)`

**入参形式**：

| 参数 | 传入方式 | 必填 | 默认值 | 说明 |
|------|----------|------|--------|------|
| code | 位置/关键字 | 是 | - | 期权代码 |
| count | 位置/关键字 | 否 | 20 | 返回条数，-500~500 |
| id | 关键字 | 否 | -1 | 起始 tick id，-1 表示最新 |

**调用示例**：

```python
# 仅必填参数（使用默认 count=20, id=-1）
r = client.optmarket.tick("usAAPL 20260320 270.0 CALL")

# 关键字传参
r = client.optmarket.tick(
    code="usAAPL 20260320 270.0 CALL",
    count=10,
    id=-1
)

# 从指定 id 向前拉取
r = client.optmarket.tick(code="usAAPL 20260320 270.0 CALL", count=50, id=12345)
```

**option_example.py 调用命令**（仅调用 tick）：

```bash
python option_example.py --opt-api tick --opt-code "usAAPL 20260320 270.0 CALL" --tick-count 20 --tick-id -1
```

### 响应格式

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "code": "usAAPL 20260320 270.0 CALL",
    "ticks": [
      {
        "id": 12345,
        "time": 1699000000000,
        "price": 1.5,
        "volume": 10,
        "side": "B"
      }
    ]
  }
}
```

---

## 5. 期权多日分时 day_min

获取期权多日分时数据（1~10 天）。

| 项目 | 说明 |
|------|------|
| **HTTP** | GET |
| **路径** | `/api/v1/optmarket/day_min` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 期权代码 |
| num | int | 否 | 天数 1~10，默认 5 |

### SDK 调用

**方法签名**：`day_min(code, num=5)`

**入参形式**：

| 参数 | 传入方式 | 必填 | 默认值 | 说明 |
|------|----------|------|--------|------|
| code | 位置/关键字 | 是 | - | 期权代码 |
| num | 位置/关键字 | 否 | 5 | 天数 1~10 |

**调用示例**：

```python
# 仅必填参数（使用默认 num=5）
r = client.optmarket.day_min("usAAPL 20260320 270.0 CALL")

# 关键字传参
r = client.optmarket.day_min(
    code="usAAPL 20260320 270.0 CALL",
    num=3
)
```

**option_example.py 调用命令**（仅调用 day_min）：

```bash
python option_example.py --opt-api day_min --opt-code "usAAPL 20260320 270.0 CALL" --day-min-num 5
```

### 响应格式

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req-xxx",
  "data": {
    "code": "usAAPL 20260320 270.0 CALL",
    "days": [
      {
        "date": "2025-03-07",
        "points": [[540, 1.5], [541, 1.52], ...]
      }
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

## 使用 option_example.py 验证

通过 `--opt-api` 指定要调用的接口，支持单独或组合调用。

### 期权相关命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--opt-code` | 期权代码 | `usAAPL 20260320 270.0 CALL` |
| `--opt-api` | 要调用的接口：orderbook/kline/quote/tick/day_min，逗号分隔或 all | - |
| `--opt-only` | 仅验证期权接口（等效于 --opt-api all） | - |
| `--kline-ktype` | K 线类型 | `1` |
| `--kline-num` | K 线数量 | `5` |
| `--kline-time` | K 线时间戳 | - |
| `--kline-start-time` | K 线开始时间戳 | - |
| `--kline-end-time` | K 线结束时间戳 | - |
| `--kline-interval` | K 线间隔 | - |
| `--kline-suspension` | K 线停牌处理 | - |
| `--tick-count` | 逐笔成交数量 (-500~500) | `10` |
| `--tick-id` | 逐笔成交起始 id，-1 表示最新 | `-1` |
| `--day-min-num` | 多日分时天数 (1~10) | `3` |
| `--quote-codes` | 批量报价代码，逗号分隔 | 使用 opt-code |
| `--quote-fields` | 批量报价返回字段，逗号分隔 | - |

### 调用示例

```bash
# 单独调用某个接口
python option_example.py --opt-api orderbook --opt-code "usAAPL 20260320 270.0 CALL"
python option_example.py --opt-api kline --opt-code "usAAPL 20260320 270.0 CALL" --kline-ktype day --kline-num 10
python option_example.py --opt-api quote --opt-code "usAAPL 20260320 270.0 CALL" --quote-fields price,hv,iv
python option_example.py --opt-api tick --opt-code "usAAPL 20260320 270.0 CALL" --tick-count 20 --tick-id -1
python option_example.py --opt-api day_min --opt-code "usAAPL 20260320 270.0 CALL" --day-min-num 5

# 组合调用多个接口（逗号分隔）
python option_example.py --opt-api kline,quote,tick --opt-code "usAAPL 20260320 270.0 CALL"

# 调用全部 5 个期权接口
python option_example.py --opt-api all --opt-code "usAAPL 20260320 270.0 CALL"

# 或使用 --opt-only（等效于 --opt-api all）
python option_example.py --opt-only --opt-code "usAAPL 20260320 270.0 CALL"
```
