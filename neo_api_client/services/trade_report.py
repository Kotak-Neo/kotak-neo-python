import httpx


class TradeReportAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def trading_report(self, order_id):
        header_params = {
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "accept": "application/json",
        }
        query_params = {}
        URL = self.api_client.configuration.get_url_details("trade_report")
        try:
            trade_report = self.rest_client.request(
                url=URL, method="GET", query_params=query_params, headers=header_params
            ).json()

            if order_id:
                output_json = {}
                if "data" in trade_report:
                    output_json["stat"] = trade_report["stat"]
                    output_json["stCode"] = trade_report["stCode"]
                    for item in trade_report["data"]:
                        if item["nOrdNo"] == order_id:
                            output_json["data"] = item
                    return output_json
                else:
                    return {"Error": "There is no trades available with the given order id"}
            else:
                return trade_report
        except httpx.HTTPError as e:
            return {"Error": e}
