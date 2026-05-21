class WealthAPI:
    def __init__(self, client):
        self.client = client

    # ProductAgreement
    def product_agreement(
        self,
        product_symbol,
        client_id,
        sub_account_id,
        product_type=17,
    ):
        if not str(product_symbol or "").strip():
            raise ValueError("product_symbol is required")
        if not client_id or int(client_id) <= 0:
            raise ValueError("client_id is required and must be positive")
        if not str(sub_account_id or "").strip():
            raise ValueError("sub_account_id is required")
        payload = {
            "productSymbol": str(product_symbol),
            "productType": int(product_type),
            "clientId": int(client_id),
            "subAccountId": str(sub_account_id),
        }
        return self.client.post("/v1/wealth/ProductAgreement", data=payload)

    # InstructionCreate
    def instruction_create(self, client_id, sub_account_id, product_type=17):
        if not client_id or int(client_id) <= 0:
            raise ValueError("client_id is required and must be positive")
        if not str(sub_account_id or "").strip():
            raise ValueError("sub_account_id is required")
        payload = {
            "clientId": int(client_id),
            "subAccountId": str(sub_account_id),
            "productType": int(product_type),
        }
        return self.client.post("/v1/wealth/InstructionCreate", data=payload)

    # Subscribe
    def rwa_note_subscribe(
        self,
        client_id,
        sub_account_id,
        symbol,
        instruction_id,
        apply_amount,
        confirmed_agreement,
        agreement_ticket,
        wallet_address=None,
        pay_type=None,
        product_type=17,
    ):
        if not client_id or int(client_id) <= 0:
            raise ValueError("client_id is required and must be positive")
        if not str(sub_account_id or "").strip():
            raise ValueError("sub_account_id is required")
        if not str(symbol or "").strip():
            raise ValueError("symbol is required")
        if not instruction_id or int(instruction_id) <= 0:
            raise ValueError("instruction_id is required and must be positive")
        if str(apply_amount or "").strip() == "":
            raise ValueError("apply_amount is required")
        if not str(agreement_ticket or "").strip():
            raise ValueError("agreement_ticket is required")
        if int(product_type) != 17:
            raise ValueError("product_type must be 17 (RWA note) for rwa_note_subscribe")

        params = {
            "symbol": str(symbol),
            "instructionId": int(instruction_id),
            "applyAmount": str(apply_amount),
        }
        if wallet_address is not None:
            params["walletAddress"] = str(wallet_address)
        if pay_type is not None:
            params["payType"] = int(pay_type)

        payload = {
            "productType": int(product_type),
            "confirmedAgreement": bool(confirmed_agreement),
            "agreementTicket": str(agreement_ticket),
            "clientId": int(client_id),
            "subAccountId": str(sub_account_id),
            "params": params,
        }
        return self.client.post("/v1/wealth/Subscribe", data=payload)

    # Rwa Redeem
    def rwa_note_redeem(
        self,
        client_id,
        sub_account_id,
        symbol,
        instruction_id,
        apply_quantity,
        wallet_address,
        confirmed_agreement,
        agreement_ticket,
        product_type=17,
    ):
        if not client_id or int(client_id) <= 0:
            raise ValueError("client_id is required and must be positive")
        if not str(sub_account_id or "").strip():
            raise ValueError("sub_account_id is required")
        if not str(symbol or "").strip():
            raise ValueError("symbol is required")
        if not instruction_id or int(instruction_id) <= 0:
            raise ValueError("instruction_id is required and must be positive")
        if str(apply_quantity or "").strip() == "":
            raise ValueError("apply_quantity is required")
        if not str(wallet_address or "").strip():
            raise ValueError("wallet_address is required")
        if not str(agreement_ticket or "").strip():
            raise ValueError("agreement_ticket is required")
        if int(product_type) != 17:
            raise ValueError("product_type must be 17 (RWA note) for rwa_note_redeem")

        params = {
            "symbol": str(symbol),
            "instructionId": int(instruction_id),
            "applyQuantity": str(apply_quantity),
            "walletAddress": str(wallet_address),
        }

        payload = {
            "productType": int(product_type),
            "confirmedAgreement": bool(confirmed_agreement),
            "agreementTicket": str(agreement_ticket),
            "clientId": int(client_id),
            "subAccountId": str(sub_account_id),
            "params": params,
        }
        return self.client.post("/v1/wealth/Redeem", data=payload)

    # OrderCancel
    def order_cancel(self, client_id, sub_account_id, order_number, product_type=17):
        if not client_id or int(client_id) <= 0:
            raise ValueError("client_id is required and must be positive")
        if not str(sub_account_id or "").strip():
            raise ValueError("sub_account_id is required")
        if not str(order_number or "").strip():
            raise ValueError("order_number is required")
        payload = {
            "productType": int(product_type),
            "clientId": int(client_id),
            "subAccountId": str(sub_account_id),
            "orderNumber": str(order_number),
        }
        return self.client.post("/v1/wealth/OrderCancel", data=payload)

    # OrderDetail
    def order_detail(self, client_id, sub_account_id, order_number, product_type=17):
        if not client_id or int(client_id) <= 0:
            raise ValueError("client_id is required and must be positive")
        if not str(sub_account_id or "").strip():
            raise ValueError("sub_account_id is required")
        if not str(order_number or "").strip():
            raise ValueError("order_number is required")
        payload = {
            "productType": int(product_type),
            "clientId": int(client_id),
            "subAccountId": str(sub_account_id),
            "orderNumber": str(order_number),
        }
        return self.client.post("/v1/wealth/OrderDetail", data=payload)

    # OrderList
    def order_list(
        self,
        client_id,
        sub_account_id,
        start=0,
        count=20,
        within_24_hours=False,
        from_date=None,
        to_date=None,
        product_types=None,
        order_direction=None,
        order_status=None,
        symbol=None,
        account=None,
    ):
        if not client_id or int(client_id) <= 0:
            raise ValueError("client_id is required and must be positive")
        if not str(sub_account_id or "").strip():
            raise ValueError("sub_account_id is required")

        payload = {
            "clientId": int(client_id),
            "subAccountId": str(sub_account_id),
            "start": int(start),
            "count": int(count),
            "within24Hours": bool(within_24_hours),
        }
        if from_date is not None:
            payload["fromDate"] = str(from_date)
        if to_date is not None:
            payload["toDate"] = str(to_date)
        if product_types is not None:
            payload["productTypes"] = [int(x) for x in product_types]
        if order_direction is not None:
            payload["orderDirection"] = [int(x) for x in order_direction]
        if order_status is not None:
            payload["orderStatus"] = [int(x) for x in order_status]
        if symbol is not None:
            payload["symbol"] = str(symbol)
        if account is not None:
            payload["account"] = str(account)
        return self.client.post("/v1/wealth/OrderList", data=payload)
