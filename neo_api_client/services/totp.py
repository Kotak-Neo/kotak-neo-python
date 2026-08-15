from json import JSONDecodeError

from neo_api_client.settings import PROD_URL


class TotpAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client
        self.totp_session = None

    def totp_login(self, mobile_number=None, ucc=None, totp=None):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "neo-fin-key": self.api_client.configuration.get_neo_fin_key(),
            "Content-Type": "application/json",
        }
        URL = (
            self.api_client.configuration.get_domain(session_init=True)
            + "/"
            + PROD_URL.get("totp_login")
        )
        body_params = {"mobileNumber": mobile_number, "ucc": ucc, "totp": totp}
        totp_login = self.rest_client.request(
            url=URL, method="POST", headers=header_params, body=body_params
        )
        try:
            totp_login_data = totp_login.json()
        except JSONDecodeError:
            return {
                "Error": "Unexpected response format. Expected JSON but received something else."
            }
        # A 2xx response can still carry an error body (e.g. invalid/empty UCC),
        # in which case "data" is absent. Only extract tokens when present, and
        # otherwise return the server's error payload as-is.
        data = totp_login_data.get("data") if isinstance(totp_login_data, dict) else None
        if 200 <= totp_login.status_code <= 299 and isinstance(data, dict):
            self.api_client.configuration.view_token = data.get("token")
            self.api_client.configuration.sid = data.get("sid")
            self.api_client.configuration.ucc = data.get("ucc")
        return totp_login_data

    def totp_validate(self, mpin=None):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "sid": self.api_client.configuration.sid,
            "Auth": self.api_client.configuration.view_token,
            "neo-fin-key": self.api_client.configuration.get_neo_fin_key(),
        }
        URL = (
            self.api_client.configuration.get_domain(session_init=True)
            + "/"
            + PROD_URL.get("totp_validate")
        )
        body_params = {"mpin": mpin}
        totp_validate = self.rest_client.request(
            url=URL, method="POST", headers=header_params, body=body_params
        )
        try:
            totp_validate_data = totp_validate.json()
        except JSONDecodeError:
            return {
                "Error": "Unexpected response format. Expected JSON but received something else."
            }
        # A 2xx response can still carry an error body (no "data"). Only extract
        # tokens when present; otherwise return the server's error payload as-is.
        data = totp_validate_data.get("data") if isinstance(totp_validate_data, dict) else None
        if 200 <= totp_validate.status_code <= 299 and isinstance(data, dict):
            self.api_client.configuration.edit_token = data.get("token")
            self.api_client.configuration.edit_sid = data.get("sid")
            self.api_client.configuration.edit_rid = data.get("rid")
            self.api_client.configuration.data_center = data.get("dataCenter")
            self.api_client.configuration.base_url = data.get("baseUrl")
            self.api_client.configuration.ucc = data.get("ucc") or self.api_client.configuration.ucc
            # Secondary source for the feed URLs, used when the dynamic
            # config service doesn't provide one (see resolve_dynamic_urls).
            self.api_client.configuration.feed_url = data.get("feedUrl")
            self.api_client.configuration.rt_url = data.get("rtUrl")
            self.api_client.configuration.resolve_dynamic_urls(self.rest_client)
        return totp_validate_data
