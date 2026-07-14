from neo_api_client.exceptions import ApiException
from neo_api_client.settings import ORDER_SOURCE
from neo_api_client.utils.order_status import check_order_not_terminal


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
        market_protection=None,
        pf=None,
        trigger_price=None,
        tag=None,
        scrip_token=None,
        square_off_type=None,
        stop_loss_type=None,
        stop_loss_value=None,
        square_off_value=None,
        last_traded_price=None,
        trailing_stop_loss=None,
        trailing_sl_value=None,
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
                "mp": market_protection,
                "pc": product,
                "pf": pf,
                "pr": price,
                "pt": order_type,
                "qt": quantity,
                "rt": validity,
                "tp": trigger_price,
                "ts": trading_symbol,
                "tt": transaction_type,
                "ig": tag,
                "tk": scrip_token,
                "sot": square_off_type,
                "slt": stop_loss_type,
                "slv": stop_loss_value,
                "sov": square_off_value,
                "lat": last_traded_price,
                "tlt": trailing_stop_loss,
                "tsv": trailing_sl_value,
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
        # An order that's already complete/traded/rejected/cancelled can't be
        # cancelled again — reject it client-side rather than sending a
        # cancel the exchange would just reject. This check is unconditional
        # (not gated by isVerify); isVerify is retained for backward
        # compatibility but no longer changes cancel_order()'s behavior. If
        # the order-book lookup itself fails, fail open and let the exchange
        # be the final arbiter (all fields needed for the cancel are already
        # in hand either way).
        try:
            _, terminal_error = check_order_not_terminal(self.api_client, order_id)
        except Exception:
            terminal_error = None
        if terminal_error:
            return terminal_error

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
            return cancel_resp.json()
        except ApiException as ex:
            return {"error": ex}
