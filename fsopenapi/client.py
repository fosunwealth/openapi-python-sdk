import uuid
import time
import json
import requests
import base64
from urllib.parse import urlparse
from .auth import SessionManager
from .crypto import CryptoManager
from .exceptions import APIError


class OpenAPIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.auth_manager = SessionManager(self.base_url, api_key)
        self._http_session = requests.Session()

        parsed_url = urlparse(self.base_url)
        self.host = parsed_url.netloc
        self.base_path = parsed_url.path.rstrip('/')

    def _request(self, method, path, data=None, params=None):
        """发送带加密和签名的请求"""
        url = f"{self.base_url}{path}"

        session_id, signing_key, encryption_key = self.auth_manager.get_valid_session()

        timestamp = str(int(time.time() * 1000))
        request_id = str(uuid.uuid4())
        nonce = str(uuid.uuid4().hex)

        query_str = ""
        if params:
            sorted_keys = sorted(params.keys())
            query_str = "&".join(f"{k}={params[k]}" for k in sorted_keys)

        full_sign_path = f"{self.base_path}{path}"

        is_market_path = path == "/status" or "/market/" in path

        # 构造统一的请求 Payload
        req_payload = {
            "encrypted": False,
            "content": data if data is not None else {}
        }

        if data is not None and not is_market_path:
            plaintext_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
            aad_str = CryptoManager.build_response_aad(session_id, timestamp, nonce)

            iv_b64, ciphertext_b64, tag_b64 = CryptoManager.encrypt_body(
                encryption_key, plaintext_bytes, aad_str.encode('utf-8')
            )

            req_payload = {
                "encrypted": True,
                "iv": iv_b64,
                "tag": tag_b64,
                "content": ciphertext_b64,
            }

        final_body_bytes = json.dumps(req_payload, separators=(',', ':')).encode('utf-8')

        signature = CryptoManager.sign(
            session_key=signing_key,
            method=method,
            path=full_sign_path,
            query=query_str,
            timestamp=timestamp,
            nonce=nonce,
            body_bytes=final_body_bytes,
        )

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-session": session_id,
            "X-Request-Id": request_id,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": signature,
        }

        response = self._http_session.request(
            method, url, data=final_body_bytes, params=params, headers=headers, verify=False
        )

        return self._handle_response(response, encryption_key, session_id, timestamp, nonce)

    def _handle_response(self, response, encryption_key, session_id, timestamp, nonce):
        """统一处理响应（支持 JSON 封装格式的响应解密）"""
        try:
            resp_payload = response.json()
        except ValueError:
            response.raise_for_status()
            return response.text

        is_encrypted = resp_payload.get("encrypted", False)
        content_obj = resp_payload.get("content")

        if is_encrypted:
            iv_b64 = resp_payload.get("iv")
            tag_b64 = resp_payload.get("tag")
            aad_str = CryptoManager.build_response_aad(session_id, timestamp, nonce)

            try:
                decrypted_bytes = CryptoManager.decrypt_body(
                    encryption_key, iv_b64, content_obj, tag_b64, aad_str.encode('utf-8')
                )
            except Exception as e:
                raise APIError(code=-1, message=f"Response decryption failed: {str(e)}")

            try:
                data = json.loads(decrypted_bytes)
            except Exception as e:
                raise APIError(code=-1, message=f"Failed to parse decrypted JSON: {str(e)}")
        else:
            data = content_obj

        if not isinstance(data, dict):
            return data

        if data.get("code") != 0:
            raise APIError(
                code=data.get("code"),
                message=data.get("message"),
                request_id=data.get("requestId"),
            )

        return data.get("data")

    def post(self, path, data=None):
        return self._request("POST", path, data=data)

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def dump_session(self):
        """将当前会话序列化为字典，可存入 JSON 文件供下次进程启动时恢复。"""
        return self.auth_manager.dump_session()

    def restore_session(self, dumped: dict) -> bool:
        """从 dump_session() 保存的字典中恢复完整会话。"""
        return self.auth_manager.restore_session(dumped)
