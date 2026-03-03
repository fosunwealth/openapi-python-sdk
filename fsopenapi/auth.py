import time
import uuid
import base64
import requests
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from .crypto import CryptoManager

class SessionManager:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session_id = None
        self.signing_key = None
        self.encryption_key = None
        self.expires_at = 0
        self.private_key = None

    def set_session(self, session_id, signing_key, encryption_key, expires_at):
        """手动设置会话信息（用于持久化复用）"""
        self.session_id = session_id
        self.signing_key = signing_key
        self.encryption_key = encryption_key
        self.expires_at = expires_at

    def dump_session(self):
        """
        将当前会话序列化为可持久化的字典（可存入 JSON 文件）。
        包含重新派生双密钥所需的全部信息：
          - sessionId / expiresAt
          - clientPrivateKey：客户端临时 ECDH 私钥（PEM，PKCS8）
          - serverPublicKey：握手时服务端返回的临时公钥（Base64）
        """
        if not self.session_id or self.private_key is None:
            return None
        priv_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        return {
            "sessionId": self.session_id,
            "expiresAt": self.expires_at,
            "clientPrivateKey": priv_pem,
            "serverPublicKey": self._server_pub_key,
        }

    def restore_session(self, dumped: dict):
        """
        从 dump_session() 返回的字典中恢复完整会话（包括重新派生双密钥）。
        如果会话已过期（提前 60 秒），返回 False，调用方应重新握手。
        """
        expires_at = dumped.get("expiresAt", 0)
        if time.time() >= (expires_at - 60):
            return False

        priv_pem = dumped.get("clientPrivateKey", "").encode("utf-8")
        server_pub_key = dumped.get("serverPublicKey")

        self.private_key = serialization.load_pem_private_key(priv_pem, password=None)
        self.session_id = dumped.get("sessionId")
        self.expires_at = expires_at
        self._server_pub_key = server_pub_key

        # 重新派生双密钥，与握手时完全一致
        self.signing_key, self.encryption_key = CryptoManager.compute_shared_secret(
            self.private_key, server_pub_key
        )
        return True

    def create_session(self):
        """执行 ECDH 握手创建会话"""
        self.private_key, client_pub_key = CryptoManager.generate_ecdh_key_pair()
        
        url = f"{self.base_url}/api/v1/auth/SessionCreate"
        
        # 严格匹配后端 mapping.SessionCreateRequest 的 JSON 标签
        payload = {
            "apiKey": str(self.api_key),
            "clientPublicKey": str(client_pub_key)
        }
        
        # 补充网关可能要求的必填 Header
        # 确保所有 Header 键名和值都是字符串，且符合网关惯例
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": str(self.api_key),
            "X-Request-Id": str(uuid.uuid4()),
            "X-timestamp": str(int(time.time() * 1000)),
            "X-source": "python-sdk",
            "X-product": "sdk",
            "X-lang": "zh-CN"
        }
        
        print(f"\n>>> [Auth Request] POST {url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Body: {json.dumps(payload, indent=2)}")

        response = requests.post(url, json=payload, headers=headers, verify=False)
        
        print(f"<<< [Auth Response] Status: {response.status_code}")
        try:
            print(f"Response Body: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except:
            print(f"Response Body: {response.text}")

        response.raise_for_status()
        
        data = response.json()
        if data.get("code") != 0:
            from .exceptions import APIError, AuthenticationError, PermissionError, CacheError
            
            error_code = data.get("code")
            error_message = data.get("message", "")
            request_id = data.get("requestId")
            
            # 根据错误码分类抛出不同的异常
            # 40001-40009: 鉴权错误
            if 40001 <= error_code <= 40009:
                raise AuthenticationError(
                    code=error_code,
                    message=error_message,
                    request_id=request_id
                )
            # 40101-40102: 权限错误
            elif 40101 <= error_code <= 40102:
                raise PermissionError(
                    code=error_code,
                    message=error_message,
                    request_id=request_id
                )
            # 50003: 缓存错误（权限同步失败时可能返回此错误）
            elif error_code == 50003:
                raise CacheError(
                    code=error_code,
                    message=f"Cache error: {error_message}. This may indicate that permission synchronization failed during session creation.",
                    request_id=request_id
                )
            # 其他错误
            else:
                raise APIError(
                    code=error_code,
                    message=error_message,
                    request_id=request_id
                )
            
        session_data = data.get("data", {})
        self.session_id = session_data.get("sessionId")
        server_pub_key = session_data.get("serverPublicKey")
        self.expires_at = session_data.get("expiresAt", 0)
        self._server_pub_key = server_pub_key  # 保存以支持 dump_session

        # 计算并派生双密钥
        self.signing_key, self.encryption_key = CryptoManager.compute_shared_secret(self.private_key, server_pub_key)
        
        # 返回完整的会话信息
        return {
            "sessionId": self.session_id,
            "serverPublicKey": server_pub_key,
            "expiresIn": session_data.get("expiresIn", 0),
            "expiresAt": self.expires_at,
        }

    def get_valid_session(self):
        """获取有效会话，如果过期则重新创建"""
        # 提前 60 秒续期
        if not self.session_id or time.time() >= (self.expires_at - 60):
            self.create_session()
        return self.session_id, self.signing_key, self.encryption_key
    
    def _get_current_timestamp(self):
        """获取当前时间戳（用于测试和内部方法）"""
        return time.time()
