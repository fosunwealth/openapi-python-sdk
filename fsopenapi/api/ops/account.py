from .prefix import ensure_ops_api_prefix


class OpsAccountAPI:
    def __init__(self, client):
        self.client = client

    def list_accounts(self):
        ensure_ops_api_prefix(self.client)
        return self.client.post("/v1/account/Accounts", data={})
