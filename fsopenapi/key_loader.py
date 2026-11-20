"""长期身份密钥加载：支持环境变量直传或文件路径（私钥文件权限校验默认关闭）。"""

import os
import stat

ENV_CLIENT_PRIVATE_KEY = "FSOPENAPI_CLIENT_PRIVATE_KEY"
ENV_CLIENT_PRIVATE_KEY_PATH = "FSOPENAPI_CLIENT_PRIVATE_KEY_PATH"
ENV_SERVER_PUBLIC_KEY = "FSOPENAPI_SERVER_PUBLIC_KEY"
ENV_SERVER_PUBLIC_KEY_PATH = "FSOPENAPI_SERVER_PUBLIC_KEY_PATH"


def _env_flag(name):
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


# 权限校验默认关闭：当前无法在 Linux 实机验证 0600 语义。
# 设置 FSOPENAPI_ENFORCE_KEY_FILE_PERMISSIONS=1 且运行在 POSIX 时才启用。
_ENFORCE_FILE_PERMISSIONS = os.name == "posix" and _env_flag(
    "FSOPENAPI_ENFORCE_KEY_FILE_PERMISSIONS"
)


def _process_group_ids():
    ids = set()
    getegid = getattr(os, "getegid", None)
    if getegid is not None:
        ids.add(getegid())
    getgroups = getattr(os, "getgroups", None)
    if getgroups is not None:
        try:
            ids.update(getgroups())
        except OSError:
            pass
    return ids


def _check_private_key_permissions(file_stat, path_env, path, label):
    if not _ENFORCE_FILE_PERMISSIONS:
        return

    mode = file_stat.st_mode
    if mode & 0o007:
        raise PermissionError(
            f"{path_env} 指向的{label}文件对其他用户可访问: {path}；"
            "请执行 chmod 600 <文件>，确保仅文件所有者可读写"
        )

    group_bits = mode & 0o070
    if group_bits:
        # 允许容器 Secret 常见的同组只读（如 0440/0640），但要求属组是进程所属组；
        # 同组可写/可执行仍然拒绝。
        if group_bits != 0o040 or file_stat.st_gid not in _process_group_ids():
            raise PermissionError(
                f"{path_env} 指向的{label}文件对同组用户权限过宽: {path}；"
                "请执行 chmod 600，或仅保留同组只读并确保属组是进程所属组"
            )


def _read_key_file(path_env, label, enforce_permissions=False):
    path = os.environ.get(path_env, "").strip()
    if not path:
        return None

    path = os.path.expanduser(path)
    try:
        with open(path, "rb") as f:
            file_stat = os.fstat(f.fileno())
            if not stat.S_ISREG(file_stat.st_mode):
                raise ValueError(f"{path_env} 必须指向普通文件: {path}")
            if enforce_permissions:
                _check_private_key_permissions(file_stat, path_env, path, label)
            data = f.read()
    except OSError as exc:
        if isinstance(exc, PermissionError):
            raise
        raise OSError(f"读取{label}失败: {path_env}={path}: {exc}") from exc

    pem = data.decode("utf-8-sig").strip()
    if not pem:
        raise ValueError(f"{path_env} 指向的{label}文件为空: {path}")
    return pem


def _resolve_key(value_env, path_env, label, enforce_permissions=False):
    # 路径模式优先；一旦设置了路径就必须成功读取，避免静默回落到环境变量明文。
    file_pem = _read_key_file(path_env, label, enforce_permissions=enforce_permissions)
    if file_pem is not None:
        return file_pem
    return os.environ.get(value_env, "").strip() or None


def load_identity_key_pems():
    """返回 (client_private_key_pem, server_public_key_pem)，未配置的为 None。"""
    return (
        _resolve_key(
            ENV_CLIENT_PRIVATE_KEY,
            ENV_CLIENT_PRIVATE_KEY_PATH,
            "客户端身份私钥",
            enforce_permissions=True,
        ),
        _resolve_key(ENV_SERVER_PUBLIC_KEY, ENV_SERVER_PUBLIC_KEY_PATH, "服务端公钥"),
    )


def missing_identity_key_configs():
    """返回缺失的配置项描述，供 SDKClient 在构造时快速失败。"""
    missing = []
    for value_env, path_env in (
        (ENV_CLIENT_PRIVATE_KEY, ENV_CLIENT_PRIVATE_KEY_PATH),
        (ENV_SERVER_PUBLIC_KEY, ENV_SERVER_PUBLIC_KEY_PATH),
    ):
        if not os.environ.get(value_env, "").strip() and not os.environ.get(path_env, "").strip():
            missing.append(f"{value_env} 或 {path_env}")
    return missing
