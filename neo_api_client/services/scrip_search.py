import io
import json

import httpx
import pandas as pd

from neo_api_client.exceptions import ApiException
from neo_api_client.utils import scrip_cache


class ScripSearch:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def scrip_search(
        self, symbol, exchange_segment, expiry, option_type, strike_price, ignore_50multiple
    ):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            if exchange_segment is not None:
                csv_content = scrip_cache.read_csv(exchange_segment)
                if csv_content is None:
                    URL = self.api_client.configuration.get_url_details("scrip_master")
                    scrip_report = self.rest_client.request(
                        url=URL, method="GET", headers=header_params
                    )
                    if scrip_report.status_code != 200:
                        return scrip_report.json()

                    data = scrip_report.json()["data"]
                    exchange_segment_csv = [
                        file
                        for file in data["filesPaths"]
                        if exchange_segment.lower() in file.lower()
                    ]

                    response = httpx.get(
                        exchange_segment_csv[0],
                        timeout=30,
                        follow_redirects=True,
                    )
                    response.raise_for_status()
                    csv_content = response.content
                    # Cache today's CSV so repeat searches on the same day
                    # reuse it instead of re-downloading; TTL expires at
                    # midnight (see neo_api_client.utils.scrip_cache).
                    scrip_cache.write_csv(exchange_segment, csv_content)

                df = pd.read_csv(
                    io.BytesIO(csv_content),
                    low_memory=False,
                )

                df = df.rename(columns=lambda x: x.strip())
                if (
                    expiry
                    and strike_price
                    and not exchange_segment.endswith("fo")
                    and exchange_segment != "mcx"
                ):
                    return {
                        "error": [
                            {
                                "code": "10300",
                                "message": "The given segment doesn't have expire and strike price",
                            }
                        ]
                    }

                if exchange_segment.endswith("fo"):
                    if not (
                        exchange_segment == "mcx"
                        or exchange_segment == "mcx_fo"
                        or exchange_segment == "bse"
                        or exchange_segment == "bse_fo"
                    ):
                        df["pExpiryDate"] = pd.to_datetime(df["pExpiryDate"], unit="s")
                        # df['pExpiryDate'] = df['pExpiryDate'] + pd.DateOffset(years=10)
                        df["pExpiryDate"] = df["pExpiryDate"] + pd.to_timedelta(315511200, unit="s")
                        df["pExpiryDate"] = df["pExpiryDate"].dt.strftime("%d%b%Y")
                    else:
                        df["pExpiryDate"] = pd.to_datetime(df["pExpiryDate"], unit="s")
                        df["pExpiryDate"] = df["pExpiryDate"].dt.strftime("%d%b%Y")
                else:
                    if exchange_segment == "mcx" or exchange_segment == "mcx_fo":
                        df["pExpiryDate"] = pd.to_datetime(df["pExpiryDate"], unit="s")
                        df["pExpiryDate"] = df["pExpiryDate"].dt.strftime("%d%b%Y")

                if symbol != "":
                    mask = df["pSymbolName"].str.lower().str.strip().str.contains(symbol)
                    df = df[mask]

                if option_type:
                    option_type = str(option_type).lower()
                    # "fut" is a Python-SDK-only alias: futures contracts in
                    # the *_fo.csv scrip-master files carry "XX" (not "CE"/
                    # "PE") in pOptionType, so map the friendlier "FUT" to
                    # the wire value "xx" (already lowercased above) before
                    # filtering.
                    option_type = [
                        "xx" if part == "fut" else part for part in option_type.split(",")
                    ]
                    df["pOptionType"] = df["pOptionType"].str.lower()
                    mask = df["pOptionType"].isin(option_type)
                    df = df[mask]

                if expiry:
                    list_expiry = expiry.split("-")
                    if len(list_expiry) > 2:
                        error = {
                            "error": [
                                {
                                    "message": "Format of expiry date is not proper. Kindly pass DDMMYYYY(01MAY2023)"
                                }
                            ]
                        }
                        return error
                    elif len(list_expiry) == 2:
                        df["pExpiryDate"] = pd.to_datetime(df["pExpiryDate"], format="%d%b%Y")
                        df = df[
                            (df["pExpiryDate"] >= pd.to_datetime(list_expiry[0]))
                            & (df["pExpiryDate"] <= pd.to_datetime(list_expiry[1]))
                        ]
                        df["pExpiryDate"] = df["pExpiryDate"].dt.strftime("%d%b%Y")
                    else:
                        df["pExpiryDate"] = pd.to_datetime(df["pExpiryDate"], format="%d%b%Y")
                        df = df[df["pExpiryDate"] == pd.to_datetime(list_expiry[0])]
                        df["pExpiryDate"] = df["pExpiryDate"].dt.strftime("%d%b%Y")

                if strike_price:
                    df["dStrikePrice;"] = df["dStrikePrice;"].astype(float)
                    if ">" in strike_price:
                        strike_price = strike_price.split(">")
                        min_strike_price = float(str(strike_price[1]) + "00.0")
                        df = df[df["dStrikePrice;"] >= min_strike_price]
                    elif "<" in strike_price:
                        strike_price = strike_price.split("<")
                        max_strike_price = float(str(strike_price[1]) + "00.0")
                        df = df[df["dStrikePrice;"] <= max_strike_price]
                    else:
                        list_strike_price = strike_price.split("-")
                        if len(list_strike_price) == 2:
                            min_strike_price, max_strike_price = (
                                float(list_strike_price[0]) * 100,
                                float(list_strike_price[1]) * 100,
                            )
                            if min_strike_price > max_strike_price:
                                error = {
                                    "error": [
                                        {
                                            "code": "10300",
                                            "message": "The minimum strike price should be less than "
                                            "the maximum strike price.",
                                        }
                                    ]
                                }
                                return error
                            else:
                                df = df[
                                    (df["dStrikePrice;"] >= min_strike_price)
                                    & (df["dStrikePrice;"] <= max_strike_price)
                                ]
                        elif len(list_strike_price) == 1:
                            if (float(list_strike_price[0]) * 100) <= 0:
                                error = {
                                    "error": [
                                        {
                                            "message": "Strike price cannot be less than 0. Please provide a valid "
                                            "value."
                                        }
                                    ]
                                }
                                return error
                            else:
                                df = df[df["dStrikePrice;"] == float(list_strike_price[0]) * 100]
                        else:
                            error = {
                                "error": [
                                    {
                                        "code": "10300",
                                        "message": "Strike price should be in the format of "
                                        "min_value-max_value or only one value.",
                                    }
                                ]
                            }
                            return error

                df = df.dropna(how="all")
                if len(df) > 0:
                    df = df.sort_values("dStrikePrice;", ascending=True)  # Add sorting step here
                    df = df.to_json(orient="records")
                    df = json.loads(df)
                    return df
                else:
                    return {
                        "message": "No data found with the given search information."
                        "Please try with other combinations."
                    }

        except ApiException as ex:
            return {"error": ex}
