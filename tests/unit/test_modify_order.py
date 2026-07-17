import json
from urllib.parse import parse_qs

from neo_api_client.services.modify_order import ModifyOrder


def _sent_body(requests_mock):
    """Decode the form-encoded jData body from the last modify request."""
    text = requests_mock.last_request.text
    jdata = parse_qs(text)["jData"][0]
    return json.loads(jdata)


def test_quick_modification_success(api_client, requests_mock):
    """Test successful order modification"""
    modify_order_api = ModifyOrder(api_client)
    url = api_client.configuration.get_url_details("modify_order")
    mock_response = {"stat": "Ok", "nOrdNo": "12345"}
    requests_mock.post(url, json=mock_response)

    result = modify_order_api.quick_modification(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        product="CNC",
        trigger_price="104.00",
        dd="NA",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert result["stat"] == "Ok"
    assert result["nOrdNo"] == "12345"


def test_quick_modification_flags_already_complete_as_400(api_client, requests_mock):
    """The backend's 'order already complete' rejection (stCode 1021) is
    annotated with status_code 400, and skips the is_verify follow-up read
    (the rejection is already definitive)."""
    modify_order_api = ModifyOrder(api_client)
    modify_url = api_client.configuration.get_url_details("modify_order")
    requests_mock.post(
        modify_url,
        json={
            "stCode": 1021,
            "errMsg": "order is completed",
            "stat": "please provide valid order number",
        },
    )

    result = modify_order_api.quick_modification(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        product="CNC",
        trigger_price="104.00",
        dd="NA",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
        is_verify=True,
    )

    assert result["status_code"] == 400
    assert result["stCode"] == 1021
    assert result["errMsg"] == "order is completed"


def test_quick_modification_already_complete_over_real_http_400(api_client, requests_mock):
    """The backend sends the 1021 rejection over an actual HTTP 400 response
    (not 200) — confirm the body is still parsed and forwarded as-is (with
    the SDK-added status_code 400), not swallowed as a transport error."""
    modify_order_api = ModifyOrder(api_client)
    modify_url = api_client.configuration.get_url_details("modify_order")
    requests_mock.post(
        modify_url,
        status_code=400,
        json={
            "stCode": 1021,
            "errMsg": "order is completed",
            "stat": "please provide valid order number",
        },
    )

    result = modify_order_api.quick_modification(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        product="CNC",
        trigger_price="104.00",
        dd="NA",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
        is_verify=True,
    )

    assert result["status_code"] == 400
    assert result["stCode"] == 1021
    assert result["errMsg"] == "order is completed"
    assert result["stat"] == "please provide valid order number"


def test_quick_modification_api_exception(api_client, monkeypatch):
    """Test order modification with API exception"""
    from neo_api_client.exceptions import ApiException

    modify_order_api = ModifyOrder(api_client)

    def fake_request(*args, **kwargs):
        raise ApiException(status=400, reason="Bad Request")

    monkeypatch.setattr(api_client.rest_client, "request", fake_request)

    result = modify_order_api.quick_modification(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        product="CNC",
        trigger_price="104.00",
        dd="NA",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert "error" in result


def test_modification_with_only_mandatory_fields(api_client, requests_mock):
    """Only mandatory fields (order_id/price/order_type/quantity/validity)
    are supplied; missing optionals are sent as None — the backend is the
    source of truth on what's required and on whether the order can still be
    modified, not a client-side order-book lookup."""
    modify_order_api = ModifyOrder(api_client)
    modify_url = api_client.configuration.get_url_details("modify_order")
    modify_route = requests_mock.post(modify_url, json={"stat": "Ok", "nOrdNo": "12345"})

    result = modify_order_api.quick_modification(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        product=None,
        trigger_price="0",
        dd="NA",
        disclosed_quantity="5",
        filled_quantity="0",
        amo="NO",
    )

    assert result["stat"] == "Ok"
    assert modify_route.call_count == 1
    body = _sent_body(requests_mock)
    assert body["pc"] is None
    assert "tk" not in body
    assert "es" not in body
    assert "ts" not in body
    assert "tt" not in body


# ---- "mp" (market protection) is always "0", not caller-configurable -------


def test_modify_order_always_sends_mp_zero(api_client, requests_mock):
    """market_protection ("mp") is hardcoded to "0" and cannot be overridden."""
    requests_mock.post(
        api_client.configuration.get_url_details("modify_order"),
        json={"stat": "Ok", "nOrdNo": "12345"},
    )

    ModifyOrder(api_client).quick_modification(
        order_id="12345",
        price="105.00",
        order_type="L",
        quantity="15",
        validity="DAY",
        product="CNC",
        trigger_price="0",
        dd="NA",
        disclosed_quantity="0",
        filled_quantity="0",
        amo="NO",
    )

    assert _sent_body(requests_mock)["mp"] == "0"


# ---- trigger_price is always sent exactly as provided ------------------------


def test_modify_trigger_price_sent_as_provided_for_limit(api_client, requests_mock):
    """A default trigger_price='0' is sent as-is for a Limit order."""
    modify_order_api = ModifyOrder(api_client)
    requests_mock.post(
        api_client.configuration.get_url_details("modify_order"),
        json={"stat": "Ok", "nOrdNo": "12345"},
    )

    result = modify_order_api.quick_modification(
        order_id="12345",
        price="2450.00",
        order_type="L",
        quantity="1",
        validity="DAY",
        product=None,
        trigger_price="0",
        dd="NA",
        disclosed_quantity="0",
        filled_quantity="0",
        amo="NO",
    )

    assert result["stat"] == "Ok"
    body = _sent_body(requests_mock)
    assert body["pt"] == "L"
    assert body["tp"] == "0"


def test_modify_explicit_trigger_always_used(api_client, requests_mock):
    """An explicitly supplied trigger_price is always sent as-is, regardless of
    order type."""
    modify_order_api = ModifyOrder(api_client)
    requests_mock.post(
        api_client.configuration.get_url_details("modify_order"),
        json={"stat": "Ok", "nOrdNo": "12345"},
    )

    modify_order_api.quick_modification(
        order_id="12345",
        price="2450.00",
        order_type="SL",
        quantity="1",
        validity="DAY",
        product=None,
        trigger_price="2480.00",  # explicit
        dd="NA",
        disclosed_quantity="0",
        filled_quantity="0",
        amo="NO",
    )

    assert _sent_body(requests_mock)["tp"] == "2480.00"


def test_modify_order_amo_none_coerced_to_no(api_client, requests_mock):
    """Modify order coerces amo=None to 'am':'NO' (mandatory field)."""
    requests_mock.post(
        api_client.configuration.get_url_details("modify_order"),
        json={"stat": "Ok", "nOrdNo": "12345"},
    )
    ModifyOrder(api_client).quick_modification(
        order_id="12345",
        price="1400",
        order_type="L",
        quantity="3",
        validity="DAY",
        product=None,
        trigger_price="0",
        dd="NA",
        disclosed_quantity="0",
        filled_quantity="0",
        amo=None,
    )
    assert _sent_body(requests_mock)["am"] == "NO"


def test_modify_order_amo_yes_is_sent(api_client, requests_mock):
    """Modify order forwards amo='YES' for AMO modifications."""
    requests_mock.post(
        api_client.configuration.get_url_details("modify_order"),
        json={"stat": "Ok", "nOrdNo": "12345"},
    )
    ModifyOrder(api_client).quick_modification(
        order_id="12345",
        price="1400",
        order_type="L",
        quantity="3",
        validity="DAY",
        product=None,
        trigger_price="0",
        dd="NA",
        disclosed_quantity="0",
        filled_quantity="0",
        amo="YES",
    )
    assert _sent_body(requests_mock)["am"] == "YES"


# ---- isVerify: confirm the final outcome after an async modify --------------


def test_modify_quick_verify_detects_exchange_rejection(api_client, requests_mock):
    """With is_verify, a modify that the exchange later rejects (ordSt=rejected
    on the order book) is surfaced as a failure, not the raw 'Ok' ack."""
    modify_url = api_client.configuration.get_url_details("modify_order")
    order_book_url = api_client.configuration.get_url_details("order_book")

    # OMS accepts the request...
    requests_mock.post(modify_url, json={"nOrdNo": "260423000183472", "stat": "Ok", "stCode": 200})
    # ...but the order book shows the exchange rejected it.
    requests_mock.get(
        order_book_url,
        json={
            "data": [
                {
                    "nOrdNo": "260423000183472",
                    "ordSt": "rejected",
                    "rejRsn": "Price is out of the current price range",
                }
            ]
        },
    )

    result = ModifyOrder(api_client).quick_modification(
        order_id="260423000183472",
        price="999999",
        order_type="L",
        quantity="1",
        validity="DAY",
        product="CNC",
        trigger_price="0",
        dd="NA",
        disclosed_quantity="0",
        filled_quantity="0",
        amo="NO",
        is_verify=True,
    )

    assert result["stat"] == "Not_Ok"
    assert "rejected" in result["Error"]
    assert result["Reason"] == "Price is out of the current price range"


def test_modify_quick_verify_passthrough_on_success(api_client, requests_mock):
    """With is_verify, an order that is live/open on the book returns the
    original successful modify response unchanged."""
    modify_url = api_client.configuration.get_url_details("modify_order")
    order_book_url = api_client.configuration.get_url_details("order_book")

    requests_mock.post(modify_url, json={"nOrdNo": "260423000183472", "stat": "Ok", "stCode": 200})
    requests_mock.get(
        order_book_url,
        json={"data": [{"nOrdNo": "260423000183472", "ordSt": "open", "rejRsn": ""}]},
    )

    result = ModifyOrder(api_client).quick_modification(
        order_id="260423000183472",
        price="1400",
        order_type="L",
        quantity="1",
        validity="DAY",
        product="CNC",
        trigger_price="0",
        dd="NA",
        disclosed_quantity="0",
        filled_quantity="0",
        amo="NO",
        is_verify=True,
    )

    assert result["stat"] == "Ok"
    assert result["stCode"] == 200


def test_modify_quick_verify_orderbook_read_failure_returns_ack(
    api_client, monkeypatch, requests_mock
):
    """If the follow-up order-book read fails, the original ack is returned
    (the confirmation must not mask the modify response)."""
    modify_url = api_client.configuration.get_url_details("modify_order")
    requests_mock.post(modify_url, json={"nOrdNo": "260423000183472", "stat": "Ok", "stCode": 200})

    import neo_api_client

    def boom(self):
        raise RuntimeError("order book unavailable")

    monkeypatch.setattr(neo_api_client.OrderReportAPI, "ordered_books", boom)

    result = ModifyOrder(api_client).quick_modification(
        order_id="260423000183472",
        price="1400",
        order_type="L",
        quantity="1",
        validity="DAY",
        product="CNC",
        trigger_price="0",
        dd="NA",
        disclosed_quantity="0",
        filled_quantity="0",
        amo="NO",
        is_verify=True,
    )

    assert result["stat"] == "Ok"  # original ack preserved


def test_modify_quick_verify_orderbook_without_data_returns_ack(api_client, requests_mock):
    """If the order book has no 'data', the original ack is returned."""
    modify_url = api_client.configuration.get_url_details("modify_order")
    order_book_url = api_client.configuration.get_url_details("order_book")
    requests_mock.post(modify_url, json={"nOrdNo": "260423000183472", "stat": "Ok", "stCode": 200})
    requests_mock.get(order_book_url, json={"stat": "Not_Ok"})

    result = ModifyOrder(api_client).quick_modification(
        order_id="260423000183472",
        price="1400",
        order_type="L",
        quantity="1",
        validity="DAY",
        product="CNC",
        trigger_price="0",
        dd="NA",
        disclosed_quantity="0",
        filled_quantity="0",
        amo="NO",
        is_verify=True,
    )

    assert result["stat"] == "Ok"
