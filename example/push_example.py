"""
Fosun Wealth OpenAPI Python SDK - 使用示例
运行前请先执行: pip install -e .
"""

import json
import logging
import os
import asyncio

from fsopenapi import APIError, AuthenticationError, CacheError, JsonFormatter, PermissionError, SDKClient

# 将 warnings.warn() (如 InsecureRequestWarning) 路由进 logging 系统
logging.captureWarnings(True)

# ============================================================
# 配置：替换为实际的网关地址和 API Key
# ============================================================
SUB_ACCOUNT_ID = "xxx"
BASE_URL = "https://openapi.fosunxcz.com"
API_KEY = "xxx"


def build_demo_logger(log_file: str = "push.log"):
    logger = logging.getLogger("push")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = JsonFormatter()

    # 终端输出
    # stream_handler = logging.StreamHandler()
    # stream_handler.setFormatter(formatter)
    # logger.addHandler(stream_handler)

    # 文件输出（UTF-8 编码）
    # mode="a" 追加模式，mode="w" 覆盖模式
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


    logger.propagate = False

    # 让 warnings.warn() 产生的日志（如 InsecureRequestWarning）也写入同一个文件
    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.handlers.clear()
    warnings_logger.addHandler(file_handler)
    warnings_logger.propagate = False

    return logger


client = SDKClient(
    logger=build_demo_logger("push_example.log"),
    logging_enable=True,
    log_body=False,
    base_url=BASE_URL,
    api_key=API_KEY,
)


def demo_session():
    client.logger.info("===== 1. 会话管理 =====")
    # session.json 通过 dump_session() 保存，包含 clientPrivateKey，
    # 下次启动时可用 restore_session() 重新派生双密钥，跳过握手。
    session_file = './session.json'
    restored = False

    if os.path.exists(session_file):
        with open(session_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        if client.restore_session(cached):
            client.logger.info("已从本地 ./session.json 恢复有效会话，跳过握手。")
            restored = True
        else:
            client.logger.error("本地会话已过期，需重新创建。")

    if not restored:
        client.session.create_session()
        dumped = client.dump_session()   # 包含 clientPrivateKey，可完整恢复
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(dumped, f, ensure_ascii=False, indent=2)
        client.logger.info("已创建新会话并保存到 ./session.json")

    current = client.session.query_session()
    client.logger.info(f"查询当前会话: {current}")

    if client.session.is_session_valid():
        client.logger.info("会话状态: 有效")

    # 主动登出（演示用，实际按需调用）
    # client.session.delete_session()

async def demo_market_push():
    client.logger.info("===== 2. 行情推送 =====")

    try:
        # 建立连接并鉴权
        await client.market_push.connect()

        # 订阅和取消订阅，需要等待1秒，有QPS限制

        # 订阅市场状态快照
        await client.market_push.subscribeMarketStatus(["cn", "us", "hk"])

        # 订阅股票报价
        await asyncio.sleep(1) 
        await client.market_push.subscribeQuote(["hk01810","hk00700"])
        
        # 订阅股票分时
        await asyncio.sleep(1)
        await client.market_push.subscribePretMarketMin(["usBABA", "usUSO", "sh600519"])

        # 通过topic 订阅股票成交明细
        await asyncio.sleep(1)
        await client.market_push.subscribe('tk', ["hk01810","hk00700"])
        
        # 取消订阅股票分时
        await asyncio.sleep(1)
        await client.market_push.unsubscribeMin(["usBABA"])

        # 订阅交易消息
        await asyncio.sleep(1)
        await client.market_push.subscribeTrade(["trade"])

        # 等待接收消息
        await asyncio.Event().wait()

    except asyncio.CancelledError:
        pass
    except Exception as e:
        client.logger.error(f"发生错误: {e}")
    finally:
        await client.market_push.close()

if __name__ == "__main__":
    try:
        demo_session()
        asyncio.run(demo_market_push())

    except KeyboardInterrupt:
        client.market_push.close()
        client.logger.info("已退出")
    except AuthenticationError as e:
        client.logger.error(f"鉴权失败: {e.code} - {e.message}")
    except PermissionError as e:
        client.logger.error(f"权限错误: {e.code} - {e.message}")
    except CacheError as e:
        client.logger.error(f"缓存错误: {e.code} - {e.message}")
    except APIError as e:
        client.logger.error(f"接口错误: {e.code} - {e.message} (requestId: {e.request_id})")
