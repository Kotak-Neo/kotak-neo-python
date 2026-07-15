from json import JSONDecodeError


class PortfolioAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def portfolio_holdings(self):
        header_params = {
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "Content-Type": "application/x-www-form-urlencoded",
            "accept": "*/*",
        }

        URL = self.api_client.configuration.get_url_details("holdings")

        portfolio_report = self.rest_client.request(
            url=URL,
            method="GET",
            headers=header_params,
        )

        try:
            return portfolio_report.json()

        except JSONDecodeError as e:
            # e.g. a 5xx with an empty/non-JSON body.
            return {
                "Error": "Unexpected response format",
                "Exception": str(e),
                "StatusCode": getattr(portfolio_report, "status_code", None),
                "ContentType": portfolio_report.headers.get("Content-Type"),
                "ResponseText": portfolio_report.text[:5000],
                "RequestURL": URL,
            }
