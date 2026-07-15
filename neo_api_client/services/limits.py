from neo_api_client.exceptions import ApiException


class LimitsAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def limit_init(self):
        header_params = {
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        query_params = {}

        # Always request limits across all segments/exchanges/products.
        body_params = {"seg": "ALL", "exch": "ALL", "prod": "ALL"}

        URL = self.api_client.configuration.get_url_details("limits")
        try:
            limits_report = self.rest_client.request(
                url=URL,
                method="POST",
                query_params=query_params,
                headers=header_params,
                body=body_params,
            )
            return limits_report.json()
        except ApiException as ex:
            return {"error": ex}
