from json import JSONDecodeError

from neo_api_client.exceptions import ApiException
from neo_api_client.settings import PROD_URL


class ClientIpAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def whatsmyip(self):
        """Fetch the client's outbound IP as seen by the Kotak backend.

        Uses the session/login host (same base as TOTP login), and the
        post-2FA credentials (Auth = trade token, Sid, Authorization).
        """
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Sid": self.api_client.configuration.edit_sid,
            "Auth": self.api_client.configuration.edit_token,
            "accept": "application/json",
        }
        URL = (
            self.api_client.configuration.get_domain(session_init=True)
            + "/"
            + PROD_URL.get("get_client_ip")
        )

        try:
            response = self.rest_client.request(url=URL, method="GET", headers=header_params)
        except ApiException as ex:
            return {"error": ex}

        try:
            return response.json()
        except JSONDecodeError:
            return {
                "Error": "Unexpected response format. Expected JSON but received something else."
            }
