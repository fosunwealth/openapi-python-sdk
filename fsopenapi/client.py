import uuid
import time
import json
import requests
import base64
from urllib.parse import urlparse, urlencode
from .auth import SessionManager
from .crypto import CryptoManager
from .exceptions import APIError

class OpenAPIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.auth_manager = SessionManager(self.base_url, api_key)
        self._http_session = requests.Session()
        
        # 解析 host 和 base_path 用于签名
        parsed_url = urlparse(self.base_url)
        self.host = parsed_url.netloc
        self.base_path = parsed_url.path.rstrip('/')

    def _request(self, method, path, data=None, params=None):
        """发送带加密和签名的请求"""
        url = f"{self.base_url}{path}"
        
        # 获取有效会话和双密钥
        session_id, signing_key, encryption_key = self.auth_manager.get_valid_session()
        
        # 准备基础参数
        timestamp = str(int(time.time() * 1000))
        request_id = str(uuid.uuid4())
        nonce = str(uuid.uuid4().hex)
        
        # 处理 Query 参数排序
        query_str = ""
        if params:
            sorted_keys = sorted(params.keys())
            parts = []
            for k in sorted_keys:
                parts.append(f"{k}={params[k]}")
            query_str = "&".join(parts)

        # 准备 Body 字节流 (使用紧凑格式 separators=(',', ':')
        plaintext_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8') if data else b""
        
        # 初始化加密相关的 Header
        encryption_headers = {}
        final_body_bytes = plaintext_bytes

        # 核心修正：签名路径必须包含 base_path (如 /api/v1)，以匹配网关 c.Path()
        full_sign_path = f"{self.base_path}{path}"

        # 行情路径：只签名、不加密（与交易/账户等鉴权方式不同）
        is_market_path = path == "/status" or "/market/" in path

        # 如果有 Body 且不是行情接口，执行 AES-GCM 加密
        if plaintext_bytes and not is_market_path:
            # 格式: X-session:%s|X-timestamp:%s|X-nonce:%s
            aad_str = f"X-session:{session_id}|X-timestamp:{timestamp}|X-nonce:{nonce}"
            
            import binascii

            iv_b64, ciphertext_b64, tag_b64 = CryptoManager.encrypt_body(
                encryption_key, plaintext_bytes, aad_str.encode('utf-8')
            )

            encryption_headers = {
                "Content-Encrypted": "true",
                "X-IV": iv_b64,
                "X-Tag": tag_b64
            }
            # 加密后的 Body 发送的是密文的原始字节
            final_body_bytes = base64.b64decode(ciphertext_b64)

        # 计算签名 (注意：签名使用的是加密后的 Body 的摘要和完整路径)
        signature = CryptoManager.sign(
            session_key=signing_key,
            method=method,
            path=full_sign_path,
            query=query_str,
            timestamp=timestamp,
            nonce=nonce,
            body_bytes=final_body_bytes
        )
        
        # 准备网关要求的 Header 字段 (严格匹配网关 c.Get 逻辑)
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-session": session_id,
            "X-Request-Id": request_id,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": signature
        }
        headers.update(encryption_headers)
        
        if encryption_headers: print(f"Encrypted: Yes (IV: {encryption_headers['X-IV']})")

        response = self._http_session.request(
            method, url, data=final_body_bytes, params=params, headers=headers, verify=False
        )

        return self._handle_response(response, encryption_key, session_id, timestamp, nonce)

    def _handle_response(self, response, encryption_key, session_id, timestamp, nonce):
        """统一处理响应和错误映射 (支持响应解密)"""
        content = response.content
        
        # 如果响应被加密，先解密
        if response.headers.get("Content-Encrypted") == "true":
            iv_b64 = response.headers.get("X-IV")
            tag_b64 = response.headers.get("X-Tag")
            # 原始逻辑使用的是 PascalCase: X-Session-Id, X-Timestamp, X-Nonce
            aad_str = f"X-Session-Id:{session_id}|X-Timestamp:{timestamp}|X-Nonce:{nonce}"
            
            try:
                content = CryptoManager.decrypt_body(
                    encryption_key, iv_b64, base64.b64encode(response.content).decode(), tag_b64, aad_str.encode('utf-8')
                )
            except Exception as e:
                import traceback
                print(f"❌ Response Decryption Failed: {e}")
                traceback.print_exc()
                # 如果解密失败，保留原样以便排查

        try:
            data = json.loads(content)
        except ValueError:
            response.raise_for_status()
            return content.decode('utf-8') if isinstance(content, bytes) else content

        if data.get("code") != 0:
            raise APIError(
                code=data.get("code"),
                message=data.get("message"),
                request_id=data.get("requestId")
            )
        
        return data.get("data")

    def post(self, path, data=None):
        return self._request("POST", path, data=data)

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def dump_session(self):
        """
        将当前会话序列化为字典，可存入 JSON 文件供下次进程启动时恢复。
        包含 sessionId、expiresAt、clientPrivateKey（PEM）、serverPublicKey（Base64）。
        """
        return self.auth_manager.dump_session()

    def restore_session(self, dumped: dict) -> bool:
        """
        从 dump_session() 保存的字典中恢复完整会话（重新派生双密钥）。
        返回 True 表示恢复成功；返回 False 表示会话已过期，需重新调用 create_session()。
        """
        return self.auth_manager.restore_session(dumped)
