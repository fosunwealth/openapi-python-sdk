import time
import uuid
import base64
import requests
import json
import os
from cryptography.hazmat.primitives import serialization
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
        self.client_nonce = None
        self.server_nonce = None
        self._server_pub_key = None

        client_priv_pem = os.environ.get("FSOPENAPI_CLIENT_PRIVATE_KEY")
        server_pub_pem = os.environ.get("FSOPENAPI_SERVER_PUBLIC_KEY")

        if not client_priv_pem or not server_pub_pem:
            self.identity_private_key = None
            self.identity_public_key = None
        else:
            self.identity_private_key = CryptoManager.load_identity_private_key(client_priv_pem)
            self.identity_public_key = CryptoManager.load_identity_public_key(server_pub_pem)

    def set_session(self, session_id, signing_key, encryption_key, expires_at):
        """手动设置会话信息（用于持久化复用）"""
        self.session_id = session_id
        self.signing_key = signing_key
        self.encryption_key = encryption_key
        self.expires_at = expires_at

    def dump_session(self):
        """
        将当前会话序列化为可持久化的字典。
        包含重新派生双密钥所需的全部信息。
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
            "clientNonce": self.client_nonce,
            "serverNonce": self.server_nonce,
        }

    def restore_session(self, dumped: dict):
        """
        从 dump_session() 返回的字典中恢复完整会话。
        如果会话已过期（提前 60 秒），返回 False。
        """
        expires_at = dumped.get("expiresAt", 0)
        if time.time() >= (expires_at - 60):
            return False

        priv_pem = dumped.get("clientPrivateKey", "").encode("utf-8")
        server_pub_key = dumped.get("serverPublicKey")
        client_nonce = dumped.get("clientNonce")
        server_nonce = dumped.get("serverNonce")

        self.private_key = serialization.load_pem_private_key(priv_pem, password=None)
        self.session_id = dumped.get("sessionId")
        self.expires_at = expires_at
        self._server_pub_key = server_pub_key
        self.client_nonce = client_nonce
        self.server_nonce = server_nonce

        self.signing_key, self.encryption_key = CryptoManager.compute_shared_secret(
            self.private_key, server_pub_key, client_nonce, server_nonce
        )
        return True

    def create_session(self):
        """执行 ECDH+ECDSA 握手创建会话"""
        if not self.identity_private_key or not self.identity_public_key:
            raise ValueError("Missing FSOPENAPI_CLIENT_PRIVATE_KEY or FSOPENAPI_SERVER_PUBLIC_KEY environment variables")

        self.private_key, client_pub_key = CryptoManager.generate_ecdh_key_pair()

        self.client_nonce = base64.b64encode(os.urandom(32)).decode('utf-8')

        signature = CryptoManager.sign_handshake(self.identity_private_key, client_pub_key, self.client_nonce)

        url = f"{self.base_url}/api/v1/auth/SessionCreate"

        payload = {
            "apiKey": str(self.api_key),
            "clientTempPublicKey": str(client_pub_key),
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": str(self.api_key),
            "X-Request-Id": str(uuid.uuid4()),
            "X-timestamp": str(int(time.time() * 1000)),
            "X-source": "python-sdk",
            "X-product": "sdk",
            "X-lang": "zh-CN",
            "X-Nonce": self.client_nonce,
            "X-Signature": signature,
        }

        response = requests.post(url, json=payload, headers=headers, verify=False)
        response.raise_for_status()

        resp = response.json()
        if "encrypted" in resp:
            data = resp.get("content") or {}
        else:
            data = resp
        if data.get("code") != 0:
            from .exceptions import AuthenticationError
            raise AuthenticationError(
                code=data.get("code", -1),
                message=data.get("message", "Handshake failed"),
            )

        session_data = data.get("data") or {}
        self.session_id = session_data.get("sessionId")
        server_pub_key = session_data.get("serverTempPublicKey")
        self.expires_at = session_data.get("expiresAt", 0)
        self._server_pub_key = server_pub_key

        server_signature = response.headers.get("X-Signature")
        self.server_nonce = response.headers.get("X-Nonce")

        if not server_signature or not self.server_nonce:
            from .exceptions import AuthenticationError
            raise AuthenticationError(code=40010, message="Missing server signature or nonce in response headers")

        if not CryptoManager.verify_handshake(self.identity_public_key, server_pub_key, self.server_nonce, server_signature):
            from .exceptions import AuthenticationError
            raise AuthenticationError(code=40011, message="Invalid server signature in handshake")

        self.signing_key, self.encryption_key = CryptoManager.compute_shared_secret(
            self.private_key, server_pub_key, self.client_nonce, self.server_nonce
        )

        return {
            "sessionId": self.session_id,
            "serverPublicKey": server_pub_key,
            "expiresIn": session_data.get("expiresIn", 0),
            "expiresAt": self.expires_at,
        }

    def get_valid_session(self):
        """获取有效会话，如果过期则重新创建"""
        if not self.session_id or time.time() >= (self.expires_at - 60):
            self.create_session()
        return self.session_id, self.signing_key, self.encryption_key

    def _get_current_timestamp(self):
        return time.time()
