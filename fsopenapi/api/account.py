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

    def sim_account_create(self):
        """创建模拟账户"""
        return self.client.post("/v1/account/SimAccountCreate", data={})

    def sim_account_reset(self, sub_account_id):
        """重置模拟账户（必填 subAccountId）"""
        payload = {"subAccountId": str(sub_account_id)}
        return self.client.post("/v1/account/SimAccountReset", data=payload)
