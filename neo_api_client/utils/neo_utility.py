import jwt

from neo_api_client.exceptions import ApiValueError
from neo_api_client.settings import PROD_URL, UAT_URL
from neo_api_client.utils.urls import (
    PROD_BASE_URL,
    SESSION_PROD_BASE_URL,
    SESSION_UAT_BASE_URL,
    UAT_BASE_URL,
)


class NeoUtility:
    """
    Project configuration (or) Params to be passed here
    """

    def __init__(
        self,
        # consumer_key=None,
        # consumer_secret=None,
        host=None,
        access_token=None,
        neo_fin_key=None,
        # base_url=None
        consumer_key=None,
    ):
        # self.consumer_key = consumer_key
        # self.consumer_secret = consumer_secret
        self.host = host
        # self.base64_token = self.convert_base64()
        self.bearer_token = access_token
        self.view_token = None
        self.sid = None
        self.userId = None
        self.edit_token = None
        self.edit_sid = None
        self.edit_rid = None
        self.login_params = None
        self.neo_fin_key = neo_fin_key
        self.data_center = None
        self.base_url = None
        self.totp_session_id = None
        self.consumer_key = consumer_key

    # def convert_base64(self):
    #     """The Base64 Token Generation.
    #     This function will generate the Base64 Token this will be used to generate the Bearer Token.
    #     Return the Token in a String Format
    #     """
    #     base64_string = str(self.consumer_key) + ":" + str(self.consumer_secret)
    #     base64_token = base64_string.encode("ascii")
    #     base64_bytes = base64.b64encode(base64_token)
    #     final_base64_token = base64_bytes.decode("ascii")
    #     return final_base64_token

    def extract_userid(self, view_token):
        if not view_token:
            raise ApiValueError(
                "View Token hasn't been Generated Kindly Call the Login Function and Try to Generate OTP"
            )
        decode_jwt = jwt.decode(view_token, options={"verify_signature": False})
        userid = decode_jwt.get("sub")
        self.userId = userid
        return userid

    def get_domain(self, session_init=False):
        # NOTE (SDK developers only): "uat" is an internal testing environment.
        # Normal usage always runs against "prod"; UAT is undocumented for users.
        host_list = ["prod", "uat"]
        if self.host.lower().strip() in host_list:
            if session_init:
                # Use SESSION URLs for TOTP login/validate only
                base_url = (
                    SESSION_UAT_BASE_URL
                    if self.host.lower().strip() == "uat"
                    else SESSION_PROD_BASE_URL
                )
            else:
                # Return the appropriate base URL based on environment
                if self.host.lower().strip() == "uat":
                    base_url = UAT_BASE_URL
                else:  # prod
                    base_url = self.base_url if self.base_url else PROD_BASE_URL
            return base_url
        else:
            raise ApiValueError("Invalid environment specified")

    def get_url_details(self, api_info):
        domain_info = self.get_domain()

        if not domain_info:
            raise ValueError(f"Base URL is not configured for host '{self.host}'")

        if self.host.lower().strip() == "prod":
            endpoint = PROD_URL.get(api_info)
        else:
            endpoint = UAT_URL.get(api_info)

        if not endpoint:
            raise ValueError(f"Endpoint mapping not found for api_info '{api_info}'")

        # Remove duplicate slashes
        domain_info = domain_info.rstrip("/")
        endpoint = endpoint.lstrip("/")

        return f"{domain_info}/{endpoint}"

    def get_neo_fin_key(self):
        # Same default neo-fin-key for both prod and uat; a caller-supplied
        # neo_fin_key always takes precedence.
        return self.neo_fin_key or "neotradeapi"
