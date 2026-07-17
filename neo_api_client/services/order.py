from neo_api_client.exceptions import ApiException
from neo_api_client.settings import ORDER_ALREADY_COMPLETE_ST_CODE, ORDER_SOURCE


class OrderAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client
        self.order_source = ORDER_SOURCE

    def order_placing(
        self,
        exchange_segment,
        product,
        price,
        order_type,
        quantity,
        validity,
        trading_symbol,
        transaction_type,
        amo=None,
        disclosed_quantity=None,
        trigger_price=None,
    ):
        try:
            header_params = {
                "Authorization": self.api_client.configuration.consumer_key,
                "Sid": self.api_client.configuration.edit_sid,
                "Auth": self.api_client.configuration.edit_token,
                "Content-Type": "application/x-www-form-urlencoded",
            }

            # "am" is mandatory on every order request; default to "NO" (regular
            # order) so a valid value is always sent. Pass "YES" for AMO orders.
            amo = amo or "NO"

            body_params = {
                "am": amo,
                "dq": disclosed_quantity,
                "es": exchange_segment,
                "mp": "0",  # Market protection is always disabled.
                "pc": product,
                "pr": price,
                "pt": order_type,
                "qt": quantity,
                "rt": validity,
                "tp": trigger_price,
                "ts": trading_symbol,
                "tt": transaction_type,
                "os": self.order_source,
            }

            URL = self.api_client.configuration.get_url_details("place_order")
            orders_resp = self.rest_client.request(
                url=URL,
                method="POST",
                query_params={},
                headers=header_params,
                body=body_params,
            )

            return orders_resp.json()
        except ApiException as ex:
            return {"error": ex}

    def order_cancelling(self, order_id, isVerify, amo=None):
        # The cancel request always goes to the backend; the exchange is the
        # source of truth on whether an order can still be cancelled.
        # isVerify is retained for backward compatibility but has no effect.
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        # "am" is mandatory; default to "NO" (regular order). Pass "YES" for AMO.
        amo = amo or "NO"
        body_params = {"on": order_id, "am": amo}

        query_params = {}
        URL = self.api_client.configuration.get_url_details("cancel_order")
        try:
            cancel_resp = self.rest_client.request(
                url=URL,
                method="POST",
                query_params=query_params,
                headers=header_params,
                body=body_params,
            )
            result = cancel_resp.json()
            if isinstance(result, dict) and result.get("stCode") == ORDER_ALREADY_COMPLETE_ST_CODE:
                result["status_code"] = 400
            return result
        except ApiException as ex:
            return {"error": ex}
