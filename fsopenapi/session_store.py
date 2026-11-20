"""会话快照的安全读写与旧版（V1 明文）快照迁移。"""

import json
import os
import tempfile

from cryptography.hazmat.primitives import serialization

from .crypto import CryptoManager

SNAPSHOT_FORMAT_VERSION = 2
DEFAULT_SNAPSHOT_MODE = 0o600


def _snapshot_password_bytes(password):
    if isinstance(password, str):
        password = password.encode("utf-8")
    if not isinstance(password, bytes) or not password:
        raise ValueError("A non-empty session snapshot password is required")
    return password


def _validate_encrypted_snapshot(snapshot):
    if not isinstance(snapshot, dict):
        raise TypeError("Session snapshot must be a dictionary")
    version = snapshot.get("formatVersion")
    if type(version) is not int or version != SNAPSHOT_FORMAT_VERSION:
        raise ValueError(
            "Only formatVersion=2 encrypted session snapshots can be written"
        )
    pem = snapshot.get("clientPrivateKey")
    if not isinstance(pem, str) or "BEGIN ENCRYPTED PRIVATE KEY" not in pem:
        raise ValueError(
            "Session snapshot clientPrivateKey must be an encrypted PKCS#8 PEM"
        )


def write_session_snapshot(path, snapshot, mode=DEFAULT_SNAPSHOT_MODE):
    """原子写入加密会话快照；POSIX 下默认 0600。

    仅接受 formatVersion=2 且私钥为加密 PEM 的快照，避免误把明文私钥写盘。
    写入使用同目录临时文件 + os.replace，失败不会留下半截文件。
    Windows 没有 POSIX mode 语义，文件继承目标目录 ACL，建议放在仅服务账号可访问的目录。
    """
    _validate_encrypted_snapshot(snapshot)
    if mode & 0o077:
        raise ValueError("Session snapshot file mode must not allow group/other access")

    # 解析符号链接，避免 os.replace 把链接本身换成普通文件、旧目标仍保留明文快照。
    path = os.path.realpath(os.fspath(path))
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(prefix=".fsopenapi-session-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            if os.name == "posix":
                os.fchmod(f.fileno(), mode)
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        if os.name == "posix":
            os.chmod(path, mode)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return path


def read_session_snapshot(path):
    """读取会话快照 JSON；返回 dict，不校验是否为加密格式。"""
    with open(os.fspath(path), "r", encoding="utf-8-sig") as f:
        snapshot = json.load(f)
    if not isinstance(snapshot, dict):
        raise ValueError("Session snapshot must be a JSON object")
    return snapshot


def _needs_permission_hardening(path):
    if os.name != "posix":
        return False
    try:
        mode = os.stat(path).st_mode
    except OSError:
        return False
    return bool(mode & 0o077)


def migrate_session_snapshot(path, password):
    """把 V1 明文快照原地重写为 V2 加密快照，并加固 V2 快照的文件权限。

    返回 True 表示文件已被重写（V1 迁移，或 V2 权限加固）；已是安全 V2 时返回 False。
    旧文件通过 os.replace 替换，不保证磁盘块层面的安全擦除。
    """
    snapshot = read_session_snapshot(path)
    version = snapshot.get("formatVersion")
    if type(version) is int and version == SNAPSHOT_FORMAT_VERSION:
        # 已是 V2 也要校验确实加密，并修正历史遗留的 0644 权限。
        _validate_encrypted_snapshot(snapshot)
        if _needs_permission_hardening(path):
            write_session_snapshot(path, snapshot)
            return True
        return False
    if version is not None and (type(version) is not int or version != 1):
        raise ValueError(f"Unsupported session snapshot formatVersion: {version!r}")

    password_bytes = _snapshot_password_bytes(password)
    pem = snapshot.get("clientPrivateKey")
    if not isinstance(pem, str) or not pem.strip():
        raise ValueError("Session snapshot is missing clientPrivateKey")

    try:
        private_key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    except Exception as exc:
        raise ValueError(
            "Cannot migrate session snapshot: clientPrivateKey is not a plaintext PEM private key"
        ) from exc

    # 迁移前先确认 key/nonces 能完成 ECDH，避免把唯一一份明文快照替换成不可恢复的文件。
    try:
        CryptoManager.compute_shared_secret(
            private_key,
            snapshot.get("serverPublicKey"),
            snapshot.get("clientNonce"),
            snapshot.get("serverNonce"),
        )
    except Exception as exc:
        raise ValueError(
            "Cannot migrate session snapshot: clientPrivateKey/serverPublicKey/nonces are inconsistent"
        ) from exc

    migrated = dict(snapshot)
    migrated["formatVersion"] = SNAPSHOT_FORMAT_VERSION
    migrated["clientPrivateKey"] = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password_bytes),
    ).decode("utf-8")
    write_session_snapshot(path, migrated)
    return True
