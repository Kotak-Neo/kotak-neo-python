from json import JSONDecodeError


class ExpiriesAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def get_expiries(self, exchange, underlying, instrument_type=None):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        query_params = {"exchange": exchange, "underlying": underlying}
        if instrument_type is not None:
            query_params["instrumentType"] = instrument_type

        URL = self.api_client.configuration.get_market_data_url("watchlist/expiries")

        expiries = self.rest_client.request(
            url=URL,
            method="GET",
            query_params=query_params,
            headers=header_params,
        )

        try:
            return expiries.json()

        except JSONDecodeError as e:
            return {
                "Error": "Unexpected response format",
                "Exception": str(e),
                "StatusCode": getattr(expiries, "status_code", None),
                "ContentType": expiries.headers.get("Content-Type"),
                "ResponseText": expiries.text[:5000],
                "RequestURL": URL,
            }
