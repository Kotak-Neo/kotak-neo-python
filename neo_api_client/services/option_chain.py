from json import JSONDecodeError


class OptionChainAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def get_option_chain(self, exchange, underlying, expiry=None, instrument_type=None, count=None):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        query_params = {"exchange": exchange, "underlying": underlying}
        if expiry is not None:
            query_params["expiry"] = expiry
        if instrument_type is not None:
            query_params["instrument_type"] = instrument_type
        if count is not None:
            query_params["count"] = count

        URL = self.api_client.configuration.get_url_details("option_chain")

        option_chain = self.rest_client.request(
            url=URL,
            method="GET",
            query_params=query_params,
            headers=header_params,
        )

        try:
            return option_chain.json()

        except JSONDecodeError as e:
            return {
                "Error": "Unexpected response format",
                "Exception": str(e),
                "StatusCode": getattr(option_chain, "status_code", None),
                "ContentType": option_chain.headers.get("Content-Type"),
                "ResponseText": option_chain.text[:5000],
                "RequestURL": URL,
            }
