import jwt
from decouple import config

from neo_api_client.__version__ import __version__
from neo_api_client.exceptions import ApiValueError
from neo_api_client.settings import PROD_URL, UAT_URL
from neo_api_client.utils.urls import (
    CONFIG_SERVICE_ENVIRONMENT_PROD,
    CONFIG_SERVICE_ENVIRONMENT_UAT,
    CONFIG_SERVICE_PLATFORM,
    CONFIG_SERVICE_URL_PROD,
    CONFIG_SERVICE_URL_UAT,
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
        self.ucc = None
        self.totp_session_id = None
        # Resolved from the dynamic config service (see resolve_dynamic_urls);
        # None until that call succeeds, so callers fall back to the
        # hardcoded SFEED_WEBSOCKET_URL default.
        self.sfeed_websocket_url = None
        # Same idea for the order feed; None until resolve_dynamic_urls()
        # succeeds, so callers fall back to the base_url-derived URL (or, if
        # that's unavailable too, the hardcoded ORDER_FEED_URL_* default).
        self.order_feed_url = None
        # Secondary sources for the two feed URLs, from totp_validate()'s
        # feedUrl/rtUrl fields (set alongside base_url/data_center). Used
        # when the dynamic config service doesn't provide sfeed_websocket_url/
        # order_feed_url, ahead of each one's own further fallback.
        self.feed_url = None
        self.rt_url = None
        self.consumer_key = consumer_key
        # SDK developers only: an optional X-Forwarded-For value attached to
        # requests in the internal UAT environment. Read from the
        # NEO_UAT_X_FORWARDED_FOR variable (see .env.dev.example). Only applied
        # when host == "uat"; ignored (and irrelevant) in production.
        self.uat_x_forwarded_for = config("NEO_UAT_X_FORWARDED_FOR", default=None)

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

    def resolve_dynamic_urls(self, rest_client):
        """Fetch this account's data-center-specific feed URLs from the dynamic
        config service, called once right after totp_validate() learns
        ``data_center``.

        The lookup is two-step: ``{data_center}_broadcast_source`` gives the
        source name (e.g. "sh", "ks") actually in use for this data center,
        which is then used to build the real endpoint keys,
        ``{data_center}_{broadcast_source}_broadcast_endpoint`` (SFeed) and
        ``{data_center}_{broadcast_source}_interactive_endpoint`` (order feed).

        Best-effort: any failure (network error, bad response, no
        ``broadcast_source`` for this data center, or no matching endpoint
        key) leaves ``sfeed_websocket_url``/``order_feed_url`` as None, and
        callers fall back to their own hardcoded defaults.
        """
        self.sfeed_websocket_url = None
        self.order_feed_url = None

        if not self.data_center:
            return

        if self.host.lower().strip() == "uat":
            url, environment = CONFIG_SERVICE_URL_UAT, CONFIG_SERVICE_ENVIRONMENT_UAT
        else:
            url, environment = CONFIG_SERVICE_URL_PROD, CONFIG_SERVICE_ENVIRONMENT_PROD

        try:
            response = rest_client.request(
                method="GET",
                url=url,
                query_params={
                    "appVersion": __version__,
                    "platform": CONFIG_SERVICE_PLATFORM,
                    "environment": environment,
                },
                timeout=5,
            )
            configs = (response.json().get("data") or {}).get("configs") or {}
            broadcast_source = configs.get(f"{self.data_center}_broadcast_source")
            if broadcast_source:
                self.sfeed_websocket_url = configs.get(
                    f"{self.data_center}_{broadcast_source}_broadcast_endpoint"
                )
                self.order_feed_url = configs.get(
                    f"{self.data_center}_{broadcast_source}_interactive_endpoint"
                )
        except Exception:
            self.sfeed_websocket_url = None
            self.order_feed_url = None

    def get_neo_fin_key(self):
        # Same default neo-fin-key for both prod and uat; a caller-supplied
        # neo_fin_key always takes precedence.
        return self.neo_fin_key or "neotradeapi"
