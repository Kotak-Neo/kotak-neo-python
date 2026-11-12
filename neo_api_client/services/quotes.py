import urllib.parse
from json import JSONDecodeError

from neo_api_client.logger import get_logger
from neo_api_client.rest import rate_limit_headers

logger = get_logger(__name__)


class QuotesAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def get_quotes(self, instrument_tokens=None, quote_type=None):
        if not quote_type:
            quote_type = "all"

        neo_symbol_str = ",".join(
            f"{item['exchange_segment']}|{item['instrument_token']}" for item in instrument_tokens
        )

        # The REST API expects the "|" and "," delimiters between multiple
        # exchange_segment|instrument_token pairs to stay literal in the path
        # segment (e.g. .../neosymbol/nse_cm|1333,nse_cm|19084/all); only
        # encode any other characters.
        encoded_neo_symbol_str = urllib.parse.quote(neo_symbol_str, safe="|,")

        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        URL = self.api_client.configuration.get_url_details("quotes_neo_symbol")
        URL = URL.format(
            neo_symbols=encoded_neo_symbol_str,
            quote_type=quote_type,
        )

        quotes = self.rest_client.request(
            url=URL,
            method="GET",
            headers=header_params,
        )

        try:
            body = quotes.json()
            limit_headers = rate_limit_headers(quotes)
            if limit_headers and isinstance(body, dict):
                body["rateLimit"] = limit_headers

            # The shared REST client's own request/response log (INFO level)
            # size-caps large bodies to a truncated preview, which can hide
            # per-quote fields (e.g. lstup_time) in a multi-instrument batch.
            # Log them explicitly here instead, uncapped: a compact per-quote
            # summary at INFO (small enough to never need truncating), and
            # the full raw response at DEBUG for deeper investigation (e.g.
            # diagnosing an unexpected lstup_time value from the backend).
            quotes_list = body if isinstance(body, list) else None
            if quotes_list is not None:
                logger.info(
                    "quotes_received",
                    count=len(quotes_list),
                    quotes=[
                        {
                            "exchange_token": q.get("exchange_token"),
                            "display_symbol": q.get("display_symbol"),
                            "exchange": q.get("exchange"),
                            "ltp": q.get("ltp"),
                            "lstup_time": q.get("lstup_time"),
                        }
                        for q in quotes_list
                        if isinstance(q, dict)
                    ],
                )
            logger.debug("quotes_response_raw", response=body)

            return body

        except JSONDecodeError as e:
            return {
                "Error": "Unexpected response format",
                "Exception": str(e),
                "StatusCode": getattr(quotes, "status_code", None),
                "ContentType": quotes.headers.get("Content-Type"),
                "ResponseText": quotes.text[:5000],
                "RequestURL": URL,
            }
