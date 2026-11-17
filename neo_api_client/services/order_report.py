import httpx

from neo_api_client.logger import get_logger
from neo_api_client.rest import rate_limit_headers, session_expired_hint

logger = get_logger(__name__)


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
            body = order_report.json()
            limit_headers = rate_limit_headers(order_report)
            if limit_headers and isinstance(body, dict):
                body["rateLimit"] = limit_headers
            hint = session_expired_hint(order_report)
            if hint and isinstance(body, dict):
                body["sessionExpired"] = hint
            return body
        except httpx.HTTPError as e:
            logger.error("order_report_request_failed", error=str(e))

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
            body = order_report.json()
            limit_headers = rate_limit_headers(order_report)
            if limit_headers and isinstance(body, dict):
                body["rateLimit"] = limit_headers
            hint = session_expired_hint(order_report)
            if hint and isinstance(body, dict):
                body["sessionExpired"] = hint
            return body
        except httpx.HTTPError as e:
            logger.error("order_report_request_failed", error=str(e))
