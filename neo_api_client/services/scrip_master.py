from neo_api_client import settings
from neo_api_client.exceptions import ApiException


class ScripMasterAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.rest_client = api_client.rest_client

    def scrip_master_init(self, exchange_segment=None):
        header_params = {
            "Authorization": self.api_client.configuration.consumer_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        URL = self.api_client.configuration.get_url_details("scrip_master")

        try:
            scrip_report = self.rest_client.request(url=URL, method="GET", headers=header_params)
            if scrip_report.status_code != 200:
                return scrip_report.json()
            scrip_report = scrip_report.json()["data"]

            if exchange_segment:
                exchange_segment = settings.exchange_segment[exchange_segment]
                exchange_segment_csv = [
                    file
                    for file in scrip_report["filesPaths"]
                    if exchange_segment.lower() in file.lower()
                ]
                if exchange_segment_csv:
                    return exchange_segment_csv[0]
                else:
                    return {"Error": "Exchange segment not found"}
            return scrip_report
        except ApiException as ex:
            return {"error": ex}
