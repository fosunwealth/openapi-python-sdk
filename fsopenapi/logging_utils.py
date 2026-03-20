import json
import logging


SDK_LOGGER_NAME = "fsopenapi"

_FULL_MASK_FIELDS = {
    "api_key",
    "apikey",
    "authorization",
    "signature",
    "x_signature",
    "xsignature",
    "clientprivatekey",
    "serverpublickey",
    "privatekey",
    "publickey",
    "signingkey",
    "encryptionkey",
}

_PARTIAL_MASK_FIELDS = {
    "session_id",
    "sessionid",
    "nonce",
    "clientnonce",
    "servernonce",
}

_RESERVED_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys()) | {"message", "asctime"}


def get_sdk_logger(logger=None):
    if logger is not None:
        return logger

    sdk_logger = logging.getLogger(SDK_LOGGER_NAME)
    if not any(isinstance(handler, logging.NullHandler) for handler in sdk_logger.handlers):
        sdk_logger.addHandler(logging.NullHandler())
    return sdk_logger


def _normalize_key(key):
    return str(key or "").replace("-", "_").lower()


def mask_value(value, keep_start=4, keep_end=4):
    if value is None:
        return None

    text = str(value)
    if not text:
        return text

    visible = keep_start + keep_end
    if len(text) <= visible:
        return "*" * min(max(len(text), 4), 8)

    return f"{text[:keep_start]}****{text[-keep_end:]}"


def sanitize_payload(payload, parent_key=None):
    if isinstance(payload, dict):
        sanitized = {}
        for key, value in payload.items():
            normalized_key = _normalize_key(key)
            if normalized_key in _FULL_MASK_FIELDS:
                sanitized[key] = "********"
            elif normalized_key in _PARTIAL_MASK_FIELDS:
                sanitized[key] = mask_value(value)
            else:
                sanitized[key] = sanitize_payload(value, parent_key=normalized_key)
        return sanitized

    if isinstance(payload, list):
        return [sanitize_payload(item, parent_key=parent_key) for item in payload]

    if isinstance(payload, tuple):
        return tuple(sanitize_payload(item, parent_key=parent_key) for item in payload)

    if parent_key in _FULL_MASK_FIELDS:
        return "********"

    if parent_key in _PARTIAL_MASK_FIELDS:
        return mask_value(payload)

    return payload


def build_log_extra(event, **fields):
    extra = {"event": event}
    for key, value in fields.items():
        if value is None:
            continue

        safe_key = key if key not in _RESERVED_RECORD_FIELDS else f"sdk_{key}"
        if isinstance(value, (dict, list, tuple)):
            extra[safe_key] = sanitize_payload(value, parent_key=_normalize_key(safe_key))
            continue

        normalized_key = _normalize_key(safe_key)
        if normalized_key in _FULL_MASK_FIELDS:
            extra[safe_key] = "********"
        elif normalized_key in _PARTIAL_MASK_FIELDS:
            extra[safe_key] = mask_value(value)
        else:
            extra[safe_key] = value
    return extra


def log_event(logger, level, event, **fields):
    exc_info = fields.pop("exc_info", None)
    stacklevel = fields.pop("stacklevel", 3)
    logger.log(level, event, extra=build_log_extra(event, **fields), exc_info=exc_info, stacklevel=stacklevel)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "logTime": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_FIELDS or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)
