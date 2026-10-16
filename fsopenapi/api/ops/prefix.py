def ensure_ops_api_prefix(client):
    prefix = (getattr(client, "api_prefix", None) or "/api").rstrip("/")
    if prefix != "/api/ops":
        raise ValueError(
            "opsTrade/opsPortfolio/opsAccount require api_prefix=/api/ops; "
            "set SDK_TYPE=ops (or construct client with api_prefix='/api/ops')"
        )
