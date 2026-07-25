from neo_api_client.exceptions import ApiException
from neo_api_client.settings import ORDER_ALREADY_COMPLETE_ST_CODE, ORDER_SOURCE


class ModifyOrder:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client
        self.order_source = ORDER_SOURCE

    def quick_modification(
        self,
        order_id,
        price,
        order_type,
        quantity,
        validity,
        trigger_price,
        disclosed_quantity,
        amo,
    ):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # "am" is mandatory; default to "NO" (regular order). Pass "YES" for AMO.
        amo = amo or "NO"

        body_params = {
            "mp": "0",  # Market protection is always disabled.
            "dq": disclosed_quantity,
            "vd": validity,
            "pr": price,
            "pt": order_type,
            "am": amo,
            "tp": trigger_price,
            "qt": quantity,
            "no": order_id,
            "os": self.order_source,
        }

        query_params = {}
        try:
            URL = self.api_client.configuration.get_url_details("modify_order")
            orders_resp = self.rest_client.request(
                url=URL,
                method="POST",
                query_params=query_params,
                headers=header_params,
                body=body_params,
            )

            modify_resp = orders_resp.json()
            if (
                isinstance(modify_resp, dict)
                and modify_resp.get("stCode") == ORDER_ALREADY_COMPLETE_ST_CODE
            ):
                modify_resp["status_code"] = 400
            return modify_resp

        except ApiException as ex:
            return {"error": ex}
