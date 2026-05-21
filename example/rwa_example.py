"""
RWA 票据接口示例：货架列表与详情。

运行前请先执行: pip install -e .

依赖环境变量（与 SDK 一致）：
  FSOPENAPI_BASE_URL、FSOPENAPI_API_KEY、
  FSOPENAPI_SERVER_PUBLIC_KEY、FSOPENAPI_CLIENT_PRIVATE_KEY

示例：
  python rwa_example.py --api list
  python rwa_example.py --api list --currency USD --start 0 --count 20
  python rwa_example.py --api detail --symbol RWA-DEMO-01
  python rwa_example.py --api all --log-file logs/rwa.log
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from fsopenapi import APIError, AuthenticationError, PermissionError, SDKClient

logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("FSOPENAPI_BASE_URL", "xxx")
API_KEY = os.environ.get("FSOPENAPI_API_KEY", "your_api_key")

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "session.json")

RWA_API_NAMES = ("list", "detail")


def setup_logging(
    level: str = "INFO",
    log_file: str = "rwa_example.log",
    max_size_mb: int = 10,
    backup_count: int = 5,
) -> None:
    """控制台 + 轮转文件，格式统一。"""
    if not os.path.isabs(log_file):
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)

    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)


def ensure_session(client: SDKClient) -> None:
    """创建或恢复会话。"""
    logger.info("===== 会话管理 =====")
    restored = False
    session_path = os.path.normpath(SESSION_FILE)

    if os.path.exists(session_path):
        with open(session_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
        if client.restore_session(cached):
            logger.info("已从本地 session 文件恢复有效会话: %s", session_path)
            restored = True
        else:
            logger.info("本地会话已过期，将重新创建。")

    if not restored:
        client.session.create_session()
        dumped = client.dump_session()
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(dumped, f, ensure_ascii=False, indent=2)
        logger.info("已创建新会话并保存到: %s", session_path)

    current = client.session.query_session()
    logger.info("查询当前会话: %s", json.dumps(current, ensure_ascii=False, default=str))
    if client.session.is_session_valid():
        logger.info("会话状态: 有效")


def log_response(label: str, data: object) -> None:
    logger.info("%s: %s", label, json.dumps(data, ensure_ascii=False, indent=2, default=str))


def run_list(client: SDKClient, args: argparse.Namespace) -> None:
    logger.info("===== RWA 票据列表 note_list =====")
    kw: dict = {}
    if args.currency is not None:
        kw["currency"] = args.currency
    if args.start is not None:
        kw["start"] = args.start
    if args.count is not None:
        kw["count"] = args.count
    r = client.rwa.note_list(**kw)
    log_response("列表响应", r)


def run_detail(client: SDKClient, args: argparse.Namespace) -> None:
    logger.info("===== RWA 票据详情 note_detail =====")
    if not args.symbol or not str(args.symbol).strip():
        logger.error("detail 接口需要非空的 --symbol")
        raise SystemExit(2)
    r = client.rwa.note_detail(args.symbol.strip())
    log_response("详情响应", r)


def parse_apis(api_arg: str | None) -> list[str]:
    if api_arg is None:
        return list(RWA_API_NAMES)
    raw = [x.strip().lower() for x in api_arg.split(",") if x.strip()]
    if "all" in raw:
        return list(RWA_API_NAMES)
    apis = [a for a in raw if a in RWA_API_NAMES]
    if not apis:
        raise SystemExit(
            f"无效的 --api: {api_arg}，可选: {', '.join(RWA_API_NAMES)}, all"
        )
    return apis


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RWA 票据接口示例（list / detail）")
    p.add_argument(
        "--api",
        metavar="API",
        help="接口：list / detail，逗号分隔，或 all（默认全部）",
    )
    p.add_argument("--symbol", help="detail 必填：票据 symbol")
    p.add_argument("--currency", help="list：币种，如 USD（可选）")
    p.add_argument("--start", type=int, help="list：分页起始（不传则 SDK 默认 0）")
    p.add_argument("--count", type=int, help="list：每页条数（不传则 SDK 默认 20）")
    p.add_argument("--log-file", default="rwa_example.log", help="日志文件路径（可相对 example 目录）")
    p.add_argument("--log-level", default="INFO", help="日志级别，如 DEBUG/INFO/WARNING")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(level=args.log_level, log_file=args.log_file)
    logger.info("启动 RWA 示例，参数: %s", args)

    apis = parse_apis(args.api)
    client = SDKClient(BASE_URL, API_KEY)

    try:
        ensure_session(client)
        if "list" in apis:
            run_list(client, args)
        if "detail" in apis:
            run_detail(client, args)
        logger.info("RWA 示例执行结束")
    except ValueError as e:
        logger.error("参数错误: %s", e)
        raise SystemExit(2) from e
    except AuthenticationError as e:
        log_response(
            "鉴权失败",
            {"code": e.code, "message": e.message, "requestId": e.request_id, "data": getattr(e, "data", None)},
        )
        raise SystemExit(1) from e
    except PermissionError as e:
        log_response(
            "权限错误",
            {"code": e.code, "message": e.message, "requestId": e.request_id, "data": getattr(e, "data", None)},
        )
        raise SystemExit(1) from e
    except APIError as e:
        log_response(
            "API 错误",
            {"code": e.code, "message": e.message, "requestId": e.request_id, "data": getattr(e, "data", None)},
        )
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
