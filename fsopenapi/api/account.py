import os

class AccountAPI:
    def __init__(self, client):
        self.client = client

    def list_accounts(self):
        """查询交易账户列表"""
        return self.client.post("/v1/account/Accounts", data={})

    def ops_accounts(self):
        """Ops可交易账户列表"""
        if os.environ.get("SDK_TYPE", "").strip().lower() != "ops":
            raise ValueError("ops_accounts() requires SDK_TYPE=ops")
        return self.client.post("/v1/account/Accounts", data={})
