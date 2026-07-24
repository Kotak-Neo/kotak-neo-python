import json


class LoginAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.base64_token = api_client.configuration.base64_token
        self.rest_client = api_client.rest_client

    def session_init(self):
        """
        Initialize a session by sending a POST request to the specified URL with OAuth2 token.

        :param URL: The URL to send the POST request to
        :type URL: str
        :return: The response from the REST client's request
        :rtype: requests.Response
        """
        header_params = {"Authorization": "Basic " + self.base64_token}
        body_params = {
            "grant_type": "client_credentials",
        }
        # if not self.api_client.configuration.base_url:
        #     return {
        #         "Message": "Error occurred to initialise the session. Base url missing or incorrect value."
        #     }
        URL = self.api_client.configuration.get_domain(session_init=True) + "oauth2/token"
        session_init = self.rest_client.request(
            url=URL, method="POST", headers=header_params, body=body_params
        )
        if session_init.is_success:
            json_resp = json.loads(session_init.text)
            self.api_client.configuration.bearer_token = json_resp.get("access_token")
            return json_resp
        else:
            return json.dumps({
                "data": {
                    "Code": session_init.status_code,
                    "Message": "Error occurred to initialise the session",
                }
            })
