import httpx


class TradeReportAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def trading_report(self):
        header_params = {
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "accept": "application/json",
        }
        query_params = {}
        URL = self.api_client.configuration.get_url_details("trade_report")
        try:
            return self.rest_client.request(
                url=URL, method="GET", query_params=query_params, headers=header_params
            ).json()
        except httpx.HTTPError as e:
            return {"Error": e}
