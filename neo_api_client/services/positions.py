import httpx

from neo_api_client.logger import get_logger
from neo_api_client.rest import rate_limit_headers

logger = get_logger(__name__)


class PositionsAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def position_init(self):
        header_params = {
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "accept": "application/json",
        }
        query_params = {}

        URL = self.api_client.configuration.get_url_details("positions")
        try:
            position_report = self.rest_client.request(
                url=URL, method="GET", query_params=query_params, headers=header_params
            )
            body = position_report.json()
            limit_headers = rate_limit_headers(position_report)
            if limit_headers and isinstance(body, dict):
                body["rateLimit"] = limit_headers
            return body
        except httpx.HTTPError as e:
            logger.error("positions_request_failed", error=str(e))
