import os
import json
import logging
import time
import uuid
from urllib.parse import urlparse

import requests
from .auth import SessionManager
from .crypto import CryptoManager
from .exceptions import APIError
from .logging_utils import get_sdk_logger, log_event, sanitize_payload


class OpenAPIClient:
    def __init__(self, base_url=None, api_key=None, logger=None, logging_enable=False, log_body=False):
        resolved_base_url = base_url or os.getenv("FSOPENAPI_BASE_URL")
        resolved_api_key = api_key or os.getenv("FSOPENAPI_API_KEY")

        if not resolved_base_url:
            raise ValueError("base_url is required. Please pass it explicitly or set FSOPENAPI_BASE_URL")
        if not resolved_api_key:
            raise ValueError("api_key is required. Please pass it explicitly or set FSOPENAPI_API_KEY")

        self.base_url = resolved_base_url.rstrip('/')
        self.api_key = resolved_api_key
        self.logger = get_sdk_logger(logger)
        self.logging_enable = logging_enable
        self.log_body = log_body
        self.auth_manager = SessionManager(
            self.base_url,
            resolved_api_key,
            logger=self.logger,
            logging_enable=logging_enable,
        )
        self._http_session = requests.Session()

        parsed_url = urlparse(self.base_url)
        self.host = parsed_url.netloc
        self.base_path = parsed_url.path.rstrip('/')
        self.api_prefix = self._resolve_api_prefix()

    def _resolve_api_prefix(self):
        sdk_type = os.getenv("SDK_TYPE", "").strip().lower()
        if sdk_type == "ops":
            return "/api/ops"
        return "/api"

    def _log(self, level, event, **fields):
        if not self.logging_enable:
            return
        log_event(self.logger, level, event, **fields)

    def _build_request_log_fields(self, data=None, params=None):
        fields = {}
        if self.log_body:
            if data is not None:
                fields["request_body"] = sanitize_payload(data)
            if params:
                fields["query_params"] = sanitize_payload(params)
        return fields

    def _build_response_log_fields(self, data=None, response_text=None):
        fields = {}
        if not self.log_body:
            return fields

        if data is not None:
            fields["response_body"] = sanitize_payload(data)
        elif response_text is not None:
            fields["response_text"] = response_text
        return fields

    def _request(self, method, path, data=None, params=None):
        """发送带加密和签名的请求"""
        if not path:
            raise ValueError("path is required")

        start_time = time.time()
        request_path = f"{self.api_prefix}{path if path.startswith('/') else f'/{path}'}"

        url = f"{self.base_url}{request_path}"

        session_id, signing_key, encryption_key = self.auth_manager.get_valid_session()

        timestamp = str(int(time.time() * 1000))
        request_id = str(uuid.uuid4())
        nonce = str(uuid.uuid4().hex)

        query_str = ""
        if params:
            sorted_keys = sorted(params.keys())
            query_str = "&".join(f"{k}={params[k]}" for k in sorted_keys)

        full_sign_path = f"{self.base_path}{request_path}"

        is_market_path = request_path == "/market/" or "/optmarket/" in request_path  
        is_encrypted = data is not None and not is_market_path

        # 构造统一的请求 Payload
        req_payload = {
            "encrypted": False,
            "content": data if data is not None else {}
        }

        if is_encrypted:
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

        self._log(
            logging.INFO,
            "request_start",
            method=method,
            path=request_path,
            request_id=request_id,
            encrypted=is_encrypted,
            is_market=is_market_path,
            **self._build_request_log_fields(data=data, params=params),
        )

        try:
            response = self._http_session.request(
                method, url, data=final_body_bytes, params=params, headers=headers, verify=False
            )
        except requests.RequestException:
            self._log(
                logging.ERROR,
                "request_http_error",
                method=method,
                path=request_path,
                request_id=request_id,
                encrypted=is_encrypted,
                is_market=is_market_path,
                cost_ms=round((time.time() - start_time) * 1000, 3),
                exc_info=True,
                **self._build_request_log_fields(data=data, params=params),
            )
            raise

        request_meta = {
            "method": method,
            "path": request_path,
            "request_id": request_id,
            "encrypted": is_encrypted,
            "is_market": is_market_path,
            "start_time": start_time,
            "request_fields": self._build_request_log_fields(data=data, params=params),
        }
        return self._handle_response(response, encryption_key, session_id, timestamp, nonce, request_meta)

    def _handle_response(self, response, encryption_key, session_id, timestamp, nonce, request_meta):
        """统一处理响应（支持 JSON 封装格式的响应解密）"""
        cost_ms = round((time.time() - request_meta["start_time"]) * 1000, 3)
        try:
            resp_payload = response.json()
        except ValueError:
            try:
                response.raise_for_status()
            except requests.RequestException:
                self._log(
                    logging.ERROR,
                    "request_http_error",
                    method=request_meta["method"],
                    path=request_meta["path"],
                    request_id=request_meta["request_id"],
                    status_code=response.status_code,
                    encrypted=request_meta["encrypted"],
                    is_market=request_meta["is_market"],
                    cost_ms=cost_ms,
                    exc_info=True,
                    **request_meta["request_fields"],
                )
                raise
            self._log(
                logging.WARNING,
                "response_non_json",
                method=request_meta["method"],
                path=request_meta["path"],
                request_id=request_meta["request_id"],
                status_code=response.status_code,
                encrypted=request_meta["encrypted"],
                is_market=request_meta["is_market"],
                cost_ms=cost_ms,
                **request_meta["request_fields"],
                **self._build_response_log_fields(response_text=response.text),
            )
            return response.text

        if "encrypted" not in resp_payload:
            data = resp_payload
        else:
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
                    self._log(
                        logging.ERROR,
                        "response_decrypt_failed",
                        method=request_meta["method"],
                        path=request_meta["path"],
                        request_id=request_meta["request_id"],
                        status_code=response.status_code,
                        encrypted=request_meta["encrypted"],
                        is_market=request_meta["is_market"],
                        cost_ms=cost_ms,
                        error_message=str(e),
                        exc_info=True,
                        **request_meta["request_fields"],
                    )
                    raise APIError(code=-1, message=f"Response decryption failed: {str(e)}")

                try:
                    data = json.loads(decrypted_bytes)
                except Exception as e:
                    self._log(
                        logging.ERROR,
                        "response_parse_failed",
                        method=request_meta["method"],
                        path=request_meta["path"],
                        request_id=request_meta["request_id"],
                        status_code=response.status_code,
                        encrypted=request_meta["encrypted"],
                        is_market=request_meta["is_market"],
                        cost_ms=cost_ms,
                        error_message=str(e),
                        exc_info=True,
                        **request_meta["request_fields"],
                    )
                    raise APIError(code=-1, message=f"Failed to parse decrypted JSON: {str(e)}")
            else:
                data = content_obj

        if not isinstance(data, dict):
            self._log(
                logging.INFO,
                "request_success",
                method=request_meta["method"],
                path=request_meta["path"],
                request_id=request_meta["request_id"],
                status_code=response.status_code,
                encrypted=request_meta["encrypted"],
                is_market=request_meta["is_market"],
                cost_ms=cost_ms,
                **request_meta["request_fields"],
                **self._build_response_log_fields(data=data),
            )
            return data

        if data.get("code") != 0:
            self._log(
                logging.WARNING,
                "response_business_error",
                method=request_meta["method"],
                path=request_meta["path"],
                request_id=request_meta["request_id"],
                status_code=response.status_code,
                code=data.get("code"),
                error_message=data.get("message"),
                encrypted=request_meta["encrypted"],
                is_market=request_meta["is_market"],
                cost_ms=cost_ms,
                **request_meta["request_fields"],
                **self._build_response_log_fields(data=data),
            )
            raise APIError(
                code=data.get("code"),
                message=data.get("message"),
                request_id=data.get("requestId"),
                data=data.get("data"),
            )

        self._log(
            logging.INFO,
            "request_success",
            method=request_meta["method"],
            path=request_meta["path"],
            request_id=request_meta["request_id"],
            status_code=response.status_code,
            code=data.get("code"),
            encrypted=request_meta["encrypted"],
            is_market=request_meta["is_market"],
            cost_ms=cost_ms,
            **request_meta["request_fields"],
            **self._build_response_log_fields(data=data),
        )
        return data

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
