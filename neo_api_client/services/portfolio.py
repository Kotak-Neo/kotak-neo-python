import requests


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

        try:
            portfolio_report = self.rest_client.request(
                url=URL,
                method="GET",
                headers=header_params,
            )

            return portfolio_report.json()

        except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")
            raise
