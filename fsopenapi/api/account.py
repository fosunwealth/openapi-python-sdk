class AccountAPI:
    def __init__(self, client):
        self.client = client

    def list_accounts(self):
        """查询交易账户列表"""
        return self.client.post("/api/v1/account/Accounts", data={})
