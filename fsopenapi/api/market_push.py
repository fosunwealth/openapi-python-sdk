# 行情推送 API

import asyncio
import websockets
from datetime import datetime
import uuid
import json
from fsopenapi.api.proto import push_pb2

Msg_Use_Proto = False

_WS_STATUS_HINTS = {
    400: "请求参数缺失，X-Api-Key 和 X-Session 均为必填项",
    401: "鉴权失败，X-Api-Key 或 X-Session 无效或已过期",
    403: "行情权限验证失败，请检查账户是否已开通对应行情服务",
    409: "该账号重复连接过多",
    500: "服务端内部错误，请稍后重试",
}

def _ws_status_hint(status_code: int) -> str:
    return _WS_STATUS_HINTS.get(status_code, f"未知错误 (HTTP {status_code})")

def _ws_status_hint_from_str(err_str: str) -> str:
    """从异常字符串中提取 HTTP 状态码并返回对应提示（兼容无 status_code 属性的异常）"""
    import re
    m = re.search(r'\b(400|401|403|409|500)\b', err_str)
    if m:
        return _ws_status_hint(int(m.group(1)))
    return ""

class MarketPushAPI:
    def __init__(self, client):
        self.client = client
        self._url = "wss://openapi-push.fosunxcz.com/msg/v1/push" # prod
        self._ws = None
        self._subscriptions = {}       # 本地记录已订阅的合约，断线后用于恢复
        self._refresh_task = None
    
    async def connect(self):
        session_id, _, _ = self.client.auth_manager.get_valid_session()
        api_key = self.client.auth_manager.api_key
        
        headers = {
            "X-Api-Key": api_key,
            "X-Session": session_id,
        }
        
        self.client.logger.info(f"正在连接到 {self._url}...")
        try:
            self._ws = await websockets.connect(self._url, additional_headers=headers)
        except websockets.exceptions.InvalidStatusCode as e:
            # websockets < 10.x
            msg = f"连接被服务端拒绝: HTTP {e.status_code} - {_ws_status_hint(e.status_code)}"
            self.client.logger.error(msg)
            raise RuntimeError(msg) from e
        except Exception as e:
            # 兼容不同版本的 websockets
            if hasattr(websockets.exceptions, 'RejectHandshake') and isinstance(e, websockets.exceptions.RejectHandshake):
                body = e.body.decode("utf-8", errors="replace") if e.body else ""
                msg = f"连接被服务端拒绝: HTTP {e.status_code} - {_ws_status_hint(e.status_code)}，错误详情: {body}"
                self.client.logger.error(msg)
                raise RuntimeError(msg) from e
            else:
                hint = _ws_status_hint_from_str(str(e))
                msg = f"连接异常: {type(e).__name__}: err: [{e}]{f' - {hint}' if hint else ''}"
                self.client.logger.error(msg)
                raise RuntimeError(msg) from e
        self.client.logger.info("WebSocket 连接成功!")

        asyncio.create_task(self._receive_loop())

    async def _receive_loop(self):
        try:
            async for message in self._ws:
                if Msg_Use_Proto:
                    s2c_msg = push_pb2.S2CMsg()
                    s2c_msg.ParseFromString(message)
                    # self.client.logger.debug(f"收到消息(proto): {s2c_msg}")

                    if s2c_msg.topic == "hb":
                        await self.send_heartbeat(s2c_msg.hbValue)
                    else:
                        for item in s2c_msg.items:
                            qt = json.loads(item.msg)
                            self.client.logger.info(
                                "received_push_msg",
                                extra={
                                    "id": s2c_msg.id,
                                    "time": s2c_msg.time,
                                    "topic": s2c_msg.topic,
                                    "hbValue": s2c_msg.hbValue,
                                    "requestid": s2c_msg.requestid,
                                    "subRep": json.loads(s2c_msg.subRep),
                                    "t": s2c_msg.t,
                                    "cache": s2c_msg.cache,
                                    "errMsg": s2c_msg.errMsg,
                                    "item_code": item.code,
                                    "data": qt
                                }
                            )     
                else:
                    msg = json.loads(message)
                    self.client.logger.info(f"收到消息(json): {msg}")
                    if msg["topic"] == "hb":
                        await self.send_heartbeat(msg["hbValue"])
        except websockets.ConnectionClosed:
            self.client.logger.info("WebSocket 连接已关闭")
        except Exception as e:
            self.client.logger.error(f"接收消息异常: {e}")
    
    async def send_heartbeat(self, hbValue):
        """
        发送心跳
        """
        if Msg_Use_Proto:
            c2s_msg = push_pb2.C2SMsg(act="hb", hbValue=hbValue)
            await self._ws.send(c2s_msg.SerializeToString())
            self.client.logger.info(f"{datetime.now()} 发送心跳请求(proto): {c2s_msg}")
        else:
            msg = {
                "act": "hb",
                "hbValue": hbValue
            }
            await self._ws.send(json.dumps(msg))
            self.client.logger.info(f"{datetime.now()} 发送心跳请求(json): {msg}")

    async def subscribe(self, topic, codes):
        """
        订阅股票代码
        :param topic: 主题 (如 'qt' 报价, 'min' 分时等)
        :param codes: 股票代码列表 (如 ['sh600519', 'usTSLA', 'hk00700'])
        """
        req_id = uuid.uuid4().hex[:8]

        if Msg_Use_Proto:
            c2s_msg = push_pb2.C2SMsg(act="sub", 
                items=[push_pb2.SubItem(topic=topic, code=codes)], requestid=req_id)
            self.client.logger.info(f"发送订阅请求(proto): {c2s_msg}")
            await self._ws.send(c2s_msg.SerializeToString())
        else:
            msg = {
                "act": "sub",
                "items": [{"topic": topic, "code": codes}],
                "requestid": req_id
             }   
            self.client.logger.info(f"发送订阅请求(json): {msg}")
            await self._ws.send(json.dumps(msg))

    async def unsubscribe(self, topic, codes):
        """
        取消订阅股票代码
        """

        req_id = uuid.uuid4().hex[:8]

        if Msg_Use_Proto:
            c2s_msg = push_pb2.C2SMsg(act="unsub", 
                items=[push_pb2.SubItem(topic=topic, code=codes)], requestid=req_id)
            self.client.logger.info(f"发送取消订阅请求(proto): {c2s_msg}")
            await self._ws.send(c2s_msg.SerializeToString())
        else:
            msg = {
                "act": "unsub",
                "items": [{"topic": topic, "code": codes}],
                "requestid": req_id
            }
            self.client.logger.info(f"发送取消订阅请求(json): {msg}")
            await self._ws.send(json.dumps(msg))

    async def close(self):
        if self._ws:
            await self._ws.close()
    
    # 订阅市场快照
    async def subscribeMarketStatus(self, codes):
        return await self.subscribe("mkt", codes)

    # 取消订阅市场快照
    async def unsubscribeMarketStatus(self, codes):
        return await self.unsubscribe("mkt", codes)

    """
    qt min tk 支持港美A的股票消息
    ob 支持港美A的股票消息，支持美股盘前盘后
    bq 支持港美A的股票消息，支持美股盘前盘后，美股夜盘
    """
    # 订阅报价
    async def subscribeQuote(self, codes):
        return await self.subscribe("qt", codes)
    
    # 取消订阅报价
    async def unsubscribeQuote(self, codes):
        return await self.unsubscribe("qt", codes)
    
    # 订阅分时
    async def subscribeMin(self, codes):
        return await self.subscribe("min", codes)

    # 取消订阅分时
    async def unsubscribeMin(self, codes):
        return await self.unsubscribe("min", codes)
    
    # 订阅成交明细
    async def subscribeTick(self, codes):
        return await self.subscribe("tk", codes)

    # 取消订阅成交明细
    async def unsubscribeTick(self, codes):
        return await self.unsubscribe("tk", codes)
    
    # 订阅经纪队列
    async def subscribeBrokerQueue(self, codes):
        return await self.subscribe("bq", codes)

    # 取消订阅经纪队列
    async def unsubscribeBrokerQueue(self, codes):
        return await self.unsubscribe("bq", codes)

    # 订阅摆盘(买卖档)
    async def subscribeOrderbook(self, codes):
        return await self.subscribe("ob", codes)

    # 取消订阅摆盘(买卖档)
    async def unsubscribeOrderbook(self, codes):
        return await self.unsubscribe("ob", codes)
    
    """
    pqt pmin ptk 支持美股盘前盘后的股票消息
    """
    # 订阅美股盘前盘后报价
    async def subscribePretMarketQuote(self, codes):
        return await self.subscribe("pqt", codes)

    # 取消订阅美股盘前盘后报价
    async def unsubscribePretMarketQuote(self, codes):
        return await self.unsubscribe("pqt", codes)

    # 订阅美股盘前盘后分时
    async def subscribePretMarketMin(self, codes):
        return await self.subscribe("pmin", codes)

    # 取消订阅美股盘前盘后分时
    async def unsubscribePretMarketMin(self, codes):
        return await self.unsubscribe("pmin", codes)

    # 订阅美股盘前盘后成交明细
    async def subscribePretMarketTick(self, codes):
        return await self.subscribe("ptk", codes)

    # 取消订阅美股盘前盘后成交明细
    async def unsubscribePretMarketTick(self, codes):
        return await self.unsubscribe("ptk", codes)

    """
    qt_nt min_nt tk_nt 支持美股夜盘的股票消息
    """
    # 订阅美股夜盘报价
    async def subscribeNightMarketQuote(self, codes):
        return await self.subscribe("qt_nt", codes)

    # 取消订阅美股夜盘报价
    async def unsubscribeNightMarketQuote(self, codes):
        return await self.unsubscribe("qt_nt", codes)

    # 订阅美股夜盘分时
    async def subscribeNightMarketMin(self, codes):
        return await self.subscribe("min_nt", codes)

    # 取消订阅美股夜盘分时
    async def unsubscribeNightMarketMin(self, codes):
        return await self.unsubscribe("min_nt", codes)

    # 订阅美股夜盘成交明细
    async def subscribeNightMarketTick(self, codes):
        return await self.subscribe("tk_nt", codes)

    # 取消订阅美股夜盘成交明细
    async def unsubscribeNightMarketTick(self, codes):
        return await self.unsubscribe("tk_nt", codes)

    """
    qt_op min_op tk_op 支持美股期权的股票消息
    """
    # 订阅美股期权报价
    async def subscribeOptionQuote(self, codes):
        return await self.subscribe("qt_op", codes)

    # 取消订阅美股期权报价
    async def unsubscribeOptionQuote(self, codes):
        return await self.unsubscribe("qt_op", codes)
    
    # 订阅美股期权分时
    async def subscribeOptionMin(self, codes):
        return await self.subscribe("min_op", codes)

    # 取消订阅美股期权分时
    async def unsubscribeOptionMin(self, codes):
        return await self.unsubscribe("min_op", codes)

    # 订阅美股期权成交明细
    async def subscribeOptionTick(self, codes):
        return await self.subscribe("tk_op", codes)

    # 取消订阅美股期权成交明细
    async def unsubscribeOptionTick(self, codes):
        return await self.unsubscribe("tk_op", codes)

    """
    trade 支持股票的交易消息
    """
    # 订阅股票交易消息
    async def subscribeTrade(self, codes):
        return await self.subscribe("trade", codes)

    # 取消订阅股票交易消息
    async def unsubscribeTrade(self, codes):
        return await self.unsubscribe("trade", codes)