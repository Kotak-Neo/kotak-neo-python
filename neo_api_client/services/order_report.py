import httpx


class OrderReportAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def ordered_books(self):
        header_params = {
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "accept": "application/json",
        }
        query_params = {}

        URL = self.api_client.configuration.get_url_details("order_book")

        try:
            order_report = self.rest_client.request(
                url=URL, method="GET", query_params=query_params, headers=header_params
            )
            return order_report.json()
        except httpx.HTTPError as e:
            # handle any exceptions that might be raised here
            print(f"Error occurred: {e}")

    def ordered_book_by_id(self, order_id):
        """Fetch a single order from the order book by its order number.

        Endpoint: GET ``<baseUrl>/quick/user/orders/<order_no>``.
        """
        header_params = {
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "accept": "application/json",
        }
        query_params = {}

        base_url = self.api_client.configuration.get_url_details("order_book")
        URL = f"{base_url.rstrip('/')}/{order_id}"

        try:
            order_report = self.rest_client.request(
                url=URL, method="GET", query_params=query_params, headers=header_params
            )
            return order_report.json()
        except httpx.HTTPError as e:
            # handle any exceptions that might be raised here
            print(f"Error occurred: {e}")
