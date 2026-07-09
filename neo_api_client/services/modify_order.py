import neo_api_client
from neo_api_client.exceptions import ApiException
from neo_api_client.settings import ORDER_SOURCE

# Order types that do not use a trigger price (a trigger is only meaningful for
# stop-loss variants). Compared against the canonical code from settings.
_NO_TRIGGER_ORDER_TYPES = {"L", "MKT"}


class ModifyOrder:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client
        self.order_source = ORDER_SOURCE

    def _verify_modification(self, order_id, modify_resp):
        """Best-effort confirmation of a modify's *final* outcome.

        A modify request is acknowledged asynchronously: the OMS returns
        ``stat: Ok`` when it accepts the request, but the exchange may reject it
        moments later (e.g. price outside the allowed band). That rejection does
        NOT appear in the modify response — it surfaces afterwards on the order
        book as ``ordSt: "rejected"``. When the caller opts in (``is_verify``),
        re-read the order book and return a failure dict if the order ended up
        rejected/cancelled; otherwise return the original modify response.
        """
        try:
            order_book_resp = neo_api_client.OrderReportAPI(self.api_client).ordered_books()
        except Exception:
            # If the follow-up read fails, don't mask the original ack.
            return modify_resp
        if not isinstance(order_book_resp, dict) or "data" not in order_book_resp:
            return modify_resp
        for item in order_book_resp["data"]:
            if item.get("nOrdNo") == order_id and item.get("ordSt") in ("rejected", "cancelled"):
                return {
                    "Error": "Order modification was rejected at the exchange. "
                    "The order status is " + str(item.get("ordSt")) + ".",
                    "Reason": item.get("rejRsn"),
                    "stat": "Not_Ok",
                    "nOrdNo": order_id,
                }
        return modify_resp

    def quick_modification(
        self,
        order_id,
        price,
        order_type,
        quantity,
        validity,
        instrument_token,
        exchange_segment,
        product,
        trading_symbol,
        transaction_type,
        trigger_price,
        dd,
        market_protection,
        disclosed_quantity,
        filled_quantity,
        amo,
        is_verify=False,
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
            "tk": instrument_token,
            "mp": market_protection,
            "pc": product,
            "dd": dd,
            "dq": disclosed_quantity,
            "vd": validity,
            "ts": trading_symbol,
            "tt": transaction_type,
            "pr": price,
            "pt": order_type,
            "fq": filled_quantity,
            "am": amo,
            "tp": trigger_price,
            "qt": quantity,
            "no": order_id,
            "es": exchange_segment,
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
            if is_verify:
                return self._verify_modification(order_id, modify_resp)
            return modify_resp

        except ApiException as ex:
            return {"error": ex}

    def modification_with_orderid(
        self,
        order_id,
        price,
        order_type,
        quantity,
        validity,
        instrument_token,
        exchange_segment,
        product,
        trading_symbol,
        transaction_type,
        trigger_price,
        dd,
        market_protection,
        disclosed_quantity,
        filled_quantity,
        amo,
        is_verify=False,
    ):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # "am" is mandatory; default to "NO" (regular order). Pass "YES" for AMO.
        amo = amo or "NO"

        order_book_resp = neo_api_client.OrderReportAPI(self.api_client).ordered_books()
        if "data" not in order_book_resp:
            return {"Message": "There is no Data in the Order Book"}
        else:
            for item in order_book_resp["data"]:
                if item["nOrdNo"] == order_id:
                    if item["ordSt"] in ["rejected", "cancelled", "complete", "traded"]:
                        if item["ordSt"] == "complete":
                            item["ordSt"] = "Traded"
                        return {
                            "Error": "The Given Order Status is "
                            + str(item["ordSt"])
                            + ", So we can't proceed further",
                            "Reason": item["rejRsn"],
                        }
                    else:
                        trading_symbol = trading_symbol or item["trdSym"]
                        instrument_token = instrument_token or item["tok"]
                        product = product or item["prod"]
                        transaction_type = transaction_type or item["trnsTp"]
                        exchange_segment = exchange_segment or item["exSeg"]
                        # Only inherit the existing order's trigger price when the
                        # caller didn't supply one AND the target order type still
                        # uses a trigger. Converting to a Limit/Market order must
                        # not carry over a stop-loss order's stale trigger price.
                        if trigger_price == "0" and order_type not in _NO_TRIGGER_ORDER_TYPES:
                            trigger_price = item["trgPrc"]

                        body_params = {
                            "tk": instrument_token,
                            "mp": market_protection,
                            "pc": product,
                            "dd": dd,
                            "dq": disclosed_quantity,
                            "vd": validity,
                            "ts": trading_symbol,
                            "tt": transaction_type,
                            "pr": price,
                            "pt": order_type,
                            "fq": filled_quantity,
                            "tp": trigger_price,
                            "qt": quantity,
                            "no": order_id,
                            "es": exchange_segment,
                            "am": amo,
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
                            if is_verify:
                                return self._verify_modification(order_id, modify_resp)
                            return modify_resp

                        except ApiException as ex:
                            return {"error": ex}
            else:
                return {
                    "Message": f"The Given Order Number is {order_id} and it is not matching with anyOrder of "
                    f"the orders"
                }
