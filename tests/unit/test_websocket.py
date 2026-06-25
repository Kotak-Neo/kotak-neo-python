"""Unit tests for WebSocket functionality."""

import pytest

from neo_api_client.websocket.NeoWebSocket import NeoWebSocket


class TestNeoWebSocket:
    """Test cases for NeoWebSocket."""

    @pytest.fixture
    def websocket(self):
        """Create a NeoWebSocket instance."""
        return NeoWebSocket(
            sid="test_sid",
            token="test_token",
            server_id="server1",
            data_center="DC1",
        )

    def test_websocket_init(self, websocket):
        """Test WebSocket initialization."""
        assert websocket.sid == "test_sid"
        assert websocket.access_token == "test_token"
        assert websocket.server_id == "server1"
        assert websocket.data_center == "DC1"
        assert websocket.hsWebsocket is None
        assert websocket.is_hsw_open == 0
        assert websocket.sub_list == []

    def test_websocket_input_validation_valid(self, websocket):
        """Test input validation with valid parameters."""
        instrument_tokens = [
            {"instrument_token": "1333", "exchange_segment": "nse_cm"},
            {"instrument_token": "11536", "exchange_segment": "nse_cm"},
        ]

        result = websocket.input_validation(instrument_tokens)
        assert result is True

    def test_websocket_input_validation_missing_token(self, websocket):
        """Test input validation with missing instrument token."""
        instrument_tokens = [
            {"exchange_segment": "nse_cm"},  # Missing instrument_token
        ]

        result = websocket.input_validation(instrument_tokens)
        assert result is False

    def test_websocket_input_validation_missing_segment(self, websocket):
        """Test input validation with missing exchange segment."""
        instrument_tokens = [
            {"instrument_token": "1333"},  # Missing exchange_segment
        ]

        result = websocket.input_validation(instrument_tokens)
        assert result is False

    def test_websocket_input_validation_empty_list(self, websocket):
        """Test input validation with empty list."""
        result = websocket.input_validation([])
        assert result is False

    def test_websocket_format_tokens_live(self, websocket):
        """Test formatting tokens for live feed."""
        instrument_token = {
            "instrument_token": "1333",
            "exchange_segment": "nse_cm",
        }

        result = websocket.format_tokens_live(instrument_token)
        assert result == "nse_cm|1333"

    def test_websocket_format_un_sub_list(self, websocket):
        """Test formatting unsubscribe list."""
        instrument_tokens = [
            {"instrument_token": "1333", "exchange_segment": "nse_cm"},
            {"instrument_token": "11536", "exchange_segment": "nse_cm"},
        ]

        result = websocket.format_un_sub_list(instrument_tokens)
        assert result == "nse_cm|1333&nse_cm|11536"

    def test_websocket_format_un_sub_list_single(self, websocket):
        """Test formatting unsubscribe list with single token."""
        instrument_tokens = [
            {"instrument_token": "1333", "exchange_segment": "nse_cm"},
        ]

        result = websocket.format_un_sub_list(instrument_tokens)
        assert result == "nse_cm|1333"

    def test_websocket_quote_type_validation_valid(self, websocket):
        """Test quote type validation with valid types."""
        valid_types = [
            "market_depth",
            "ohlc",
            "ltp",
            "52w",
            "circuit_limits",
            "scrip_details",
        ]

        for quote_type in valid_types:
            result = websocket.quote_type_validation(quote_type)
            assert result is True

    def test_websocket_quote_type_validation_case_insensitive(self, websocket):
        """Test quote type validation is case insensitive."""
        result = websocket.quote_type_validation("MARKET_DEPTH")
        assert result is True

        result = websocket.quote_type_validation("Market_Depth")
        assert result is True

    def test_websocket_quote_type_validation_invalid(self, websocket):
        """Test quote type validation with invalid type."""
        result = websocket.quote_type_validation("invalid_type")
        assert result is False

    def test_websocket_quote_type_validation_none(self, websocket):
        """Test quote type validation with None."""
        result = websocket.quote_type_validation(None)
        assert result is True  # None is acceptable

    def test_websocket_callbacks_none_by_default(self, websocket):
        """Test that callbacks are None by default."""
        assert websocket.on_message is None
        assert websocket.on_error is None
        assert websocket.on_close is None
        assert websocket.on_open is None

    def test_websocket_set_callbacks(self, websocket):
        """Test setting callbacks."""

        def on_message(msg):
            pass

        def on_error(err):
            pass

        def on_close():
            pass

        def on_open():
            pass

        websocket.on_message = on_message
        websocket.on_error = on_error
        websocket.on_close = on_close
        websocket.on_open = on_open

        assert websocket.on_message == on_message
        assert websocket.on_error == on_error
        assert websocket.on_close == on_close
        assert websocket.on_open == on_open

    def test_websocket_channel_segregation(self, websocket):
        """Test channel segregation for tokens."""
        tmp_token_list = [
            {
                "1333": {
                    "instrument_token": "1333",
                    "exchange_segment": "nse_cm",
                    "subscription_type": "mws",
                }
            },
            {
                "11536": {
                    "instrument_token": "11536",
                    "exchange_segment": "nse_cm",
                    "subscription_type": "mws",
                }
            },
        ]

        result = websocket.channel_segregation(tmp_token_list)

        # Should assign to channel 2 (first available)
        assert 2 in result
        assert len(result[2]) == 2

    def test_websocket_channel_segregation_overflow(self, websocket):
        """Test channel segregation with more than 200 tokens."""
        # Create 250 tokens
        tmp_token_list = [
            {
                str(i): {
                    "instrument_token": str(i),
                    "exchange_segment": "nse_cm",
                    "subscription_type": "mws",
                }
            }
            for i in range(250)
        ]

        result = websocket.channel_segregation(tmp_token_list)

        # Should use multiple channels
        total_tokens = sum(len(tokens) for tokens in result.values())
        assert total_tokens == 250

    def test_websocket_remove_items(self, websocket):
        """Test removing items from subscription list."""
        # Setup subscription list
        websocket.sub_list = [
            {
                "1333": {
                    "instrument_token": "1333",
                    "exchange_segment": "nse_cm",
                    "subscription_type": "mws",
                }
            },
            {
                "11536": {
                    "instrument_token": "11536",
                    "exchange_segment": "nse_cm",
                    "subscription_type": "mws",
                }
            },
        ]

        websocket.channel_tokens = {
            2: [
                {
                    "1333": {
                        "instrument_token": "1333",
                        "exchange_segment": "nse_cm",
                        "subscription_type": "mws",
                    }
                },
            ]
        }

        # Remove one item
        un_sub_json = [
            {
                "1333": {
                    "instrument_token": "1333",
                    "exchange_segment": "nse_cm",
                    "subscription_type": "mws",
                }
            },
        ]

        websocket.remove_items(un_sub_json)

        # Check that item was removed
        assert len(websocket.sub_list) == 1
        assert websocket.sub_list[0]["11536"]["instrument_token"] == "11536"

    def test_websocket_prepare_un_sub(self, websocket):
        """Test preparing unsubscribe data."""
        websocket.channel_tokens = {
            2: [
                {
                    "1333": {
                        "instrument_token": "1333",
                        "exchange_segment": "nse_cm",
                        "subscription_type": "mws",
                    }
                },
            ]
        }

        websocket.prepare_un_sub()

        # Should create un_sub_channel_token
        assert len(websocket.un_sub_channel_token) > 0
        assert "2-mwu" in websocket.un_sub_channel_token

    def test_websocket_is_message_for_subscription(self, websocket):
        """Test checking if message is for subscription."""
        websocket.sub_list = [
            {
                "1333": {
                    "instrument_token": "1333",
                    "exchange_segment": "nse_cm",
                    "subscription_type": "mws",
                }
            },
        ]

        # Message with matching token
        message = [{"tk": "1333", "ltp": "785.50"}]
        result = websocket.is_message_for_subscription(message)
        assert result is True

        # Message without matching token
        message = [{"tk": "9999", "ltp": "100.00"}]
        result = websocket.is_message_for_subscription(message)
        assert result is False

    def test_websocket_append_ohlc_data(self, websocket):
        """Test appending OHLC data."""
        new_dict = {
            "open": "100.00",
            "high": "105.00",
            "low": "99.00",
            "close": "102.00",
            "ltp": "103.00",
        }

        result = websocket.append_ohlc_data(new_dict)

        assert "ohlc" in result
        assert result["ohlc"]["open"] == "100.00"
        assert result["ohlc"]["high"] == "105.00"
        assert result["ohlc"]["low"] == "99.00"
        assert result["ohlc"]["close"] == "102.00"
        assert "open" not in result  # Should be removed from top level
        assert result["ltp"] == "103.00"  # Should remain

    def test_websocket_quote_type_filter_ltp(self, websocket):
        """Test quote type filter for LTP."""
        new_dict = {
            "instrument_token": "1333",
            "trading_symbol": "HDFCBANK-EQ",
            "exchange_segment": "nse_cm",
            "last_traded_price": "785.50",
            "ohlc": {"open": "780.00"},
        }

        result = websocket.quote_type_filter(new_dict, "ltp")

        assert "ltp" in result
        assert result["ltp"] == "785.50"
        assert "ohlc" not in result  # Should not include ohlc for ltp

    def test_websocket_quote_type_filter_ohlc(self, websocket):
        """Test quote type filter for OHLC."""
        new_dict = {
            "instrument_token": "1333",
            "trading_symbol": "HDFCBANK-EQ",
            "exchange_segment": "nse_cm",
            "last_traded_price": "785.50",
            "ohlc": {
                "open": "780.00",
                "high": "790.00",
                "low": "775.00",
                "close": "785.00",
            },
        }

        result = websocket.quote_type_filter(new_dict, "ohlc")

        assert "ohlc" in result
        assert result["ohlc"]["open"] == "780.00"
        assert "last_traded_price" not in result  # Should not include other fields

    def test_websocket_quote_type_filter_52w(self, websocket):
        """Test quote type filter for 52 week high/low."""
        new_dict = {
            "instrument_token": "1333",
            "trading_symbol": "HDFCBANK-EQ",
            "exchange_segment": "nse_cm",
            "52week_high": "900.00",
            "52week_low": "700.00",
            "last_traded_price": "785.50",
        }

        result = websocket.quote_type_filter(new_dict, "52w")

        assert "52week_high" in result
        assert "52week_low" in result
        assert result["52week_high"] == "900.00"
        assert "last_traded_price" not in result

    def test_websocket_data_center_urls(self):
        """Test WebSocket URL selection based on data center."""
        data_centers = {
            "adc": "ADC",
            "e21": "E21",
            "e22": "E22",
            "e41": "E41",
            "e43": "E43",
        }

        for dc_key, _dc_name in data_centers.items():
            ws = NeoWebSocket(
                sid="test_sid",
                token="test_token",
                server_id="server1",
                data_center=dc_key,
            )
            assert ws.data_center == dc_key
