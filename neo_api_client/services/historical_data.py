from json import JSONDecodeError


class HistoricalDataAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def get_historical_data(self, neosymbol, interval, from_date=None, to_date=None):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Wire query params are lowercase (fromdate/todate), unlike this
        # method's snake_case kwargs -- matching the real backend endpoint,
        # not the SDK's own naming convention.
        query_params = {"neosymbol": neosymbol, "interval": interval}
        if from_date is not None:
            query_params["fromdate"] = from_date
        if to_date is not None:
            query_params["todate"] = to_date

        URL = self.api_client.configuration.get_market_data_url("historical/details")

        historical_data = self.rest_client.request(
            url=URL,
            method="GET",
            query_params=query_params,
            headers=header_params,
        )

        try:
            return historical_data.json()

        except JSONDecodeError as e:
            return {
                "Error": "Unexpected response format",
                "Exception": str(e),
                "StatusCode": getattr(historical_data, "status_code", None),
                "ContentType": historical_data.headers.get("Content-Type"),
                "ResponseText": historical_data.text[:5000],
                "RequestURL": URL,
            }
