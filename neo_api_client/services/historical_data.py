from json import JSONDecodeError

from neo_api_client.rest import rate_limit_headers


class HistoricalDataAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def get_historical_data(self, neosymbol, interval, from_date, to_date):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Wire query params are lowercase (fromdate/todate), unlike this
        # method's snake_case kwargs -- matching the real backend endpoint,
        # not the SDK's own naming convention.
        query_params = {
            "neosymbol": neosymbol,
            "interval": interval,
            "fromdate": from_date,
            "todate": to_date,
        }

        URL = self.api_client.configuration.get_url_details("historical_data")

        historical_data = self.rest_client.request(
            url=URL,
            method="GET",
            query_params=query_params,
            headers=header_params,
        )

        try:
            body = historical_data.json()
            limit_headers = rate_limit_headers(historical_data)
            if limit_headers and isinstance(body, dict):
                body["rateLimit"] = limit_headers
            return body

        except JSONDecodeError as e:
            return {
                "Error": "Unexpected response format",
                "Exception": str(e),
                "StatusCode": getattr(historical_data, "status_code", None),
                "ContentType": historical_data.headers.get("Content-Type"),
                "ResponseText": historical_data.text[:5000],
                "RequestURL": URL,
            }
