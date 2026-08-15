from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, NoReturn

from neo_api_client import req_data_validation, settings
from neo_api_client.api_client import ApiClient
from neo_api_client.services.client_ip import ClientIpAPI
from neo_api_client.services.limits import LimitsAPI
from neo_api_client.services.margin import MarginAPI
from neo_api_client.services.modify_order import ModifyOrder
from neo_api_client.services.order import OrderAPI
from neo_api_client.services.order_history import OrderHistoryAPI
from neo_api_client.services.order_report import OrderReportAPI
from neo_api_client.services.portfolio import PortfolioAPI
from neo_api_client.services.positions import PositionsAPI
from neo_api_client.services.quotes import QuotesAPI
from neo_api_client.services.scrip_master import ScripMasterAPI
from neo_api_client.services.scrip_search import ScripSearch
from neo_api_client.services.totp import TotpAPI
from neo_api_client.services.trade_report import TradeReportAPI
from neo_api_client.utils.neo_utility import NeoUtility
from neo_api_client.utils.urls import (
    ORDER_FEED_URL_E21,
    ORDER_FEED_URL_E22,
    ORDER_FEED_URL_E41,
    ORDER_FEED_URL_E43,
)

# Last-resort order-feed URL, used only when neither the dynamic config
# service nor totp_validate()'s baseUrl gave us an endpoint for this data
# center.
_ORDER_FEED_URL_BY_DATA_CENTER = {
    "E21": ORDER_FEED_URL_E21,
    "E22": ORDER_FEED_URL_E22,
    "E41": ORDER_FEED_URL_E41,
    "E43": ORDER_FEED_URL_E43,
}

if TYPE_CHECKING:
    from neo_api_client.websocket.feed import SFeedWebSocket
    from neo_api_client.websocket.orderfeed import OrderFeedWebSocket


class NeoAPI:
    """
    A class representing the NeoAPI client for Kotak Neo Trading Platform.

    The `NeoAPI` class provides methods to initialize the API client, authenticate using TOTP,
    place orders, manage portfolio, and access real-time market data.

    Attributes:
        environment (str): The environment for the API client. Defaults to 'prod'.
        consumer_key (str): Consumer key token from NEO app Trade API card (optional for tracking).
        access_token (str): Pre-authenticated access token (optional).
        neo_fin_key (str): Financial key for tracking purpose (optional).
        configuration: The configuration for the API client.
        api_client (ApiClient): The API client instance.

    Authentication Flow:
        1. Get consumer_key from NEO app (More → Trade API → Generate application)
        2. Initialize NeoAPI with consumer_key
        3. Call totp_login() with mobile, UCC, and TOTP code
        4. Call totp_validate() with MPIN to get trading access

    Example:
        ```python
        from neo_api_client import NeoAPI

        # Initialize client
        client = NeoAPI(
            consumer_key='your-token-from-neo-app',
            environment='prod'
        )

        # Step 1: Login with TOTP
        client.totp_login(
            mobile_number='+919876543210',
            ucc='ABC123',
            totp='123456'
        )

        # Step 2: Validate with MPIN
        client.totp_validate(mpin='123456')

        # Now you can place orders, get quotes, etc.
        ```
    """

    def __init__(
        self,
        consumer_key: str | None = None,
        environment: str = "prod",
        access_token: str | None = None,
        neo_fin_key: str | None = None,
    ) -> None:
        """
        Initializes the NeoAPI client with authentication credentials.

        Parameters:
            consumer_key (str): **REQUIRED** - Consumer key token from NEO app Trade API card.
                How to get: Login to NEO app/web → More tab → Trade API → Generate application → Copy token.
                This token is used in the Authorization header for all API requests.
                Without this, authentication will fail.
            environment (str): The environment to connect to. Default: 'prod' (production).
            access_token (str, optional): Pre-authenticated access token (if you already have one).
                Default: None (use TOTP authentication flow instead)
            neo_fin_key (str, optional): Financial key for tracking purpose.
                Default: None

        WebSocket Callbacks:
            You can set these callback functions after initialization:
            - self.on_message: Callback for incoming WebSocket messages
            - self.on_error: Callback for WebSocket errors
            - self.on_close: Callback for WebSocket connection close
            - self.on_open: Callback for WebSocket connection open

        Example:
            ```python
            # Initialize with consumer key from NEO app
            client = NeoAPI(
                consumer_key='your-token-from-neo-app',
                environment='prod'
            )
            ```

        Note:
            After initialization, you need to authenticate using:
            1. client.totp_login(mobile_number, ucc, totp)
            2. client.totp_validate(mpin)
        """

        self.on_message = None
        self.on_error = None
        self.on_close = None
        self.on_open = None

        if not access_token:
            # neo_api_client.req_data_validation.validate_configuration(consumer_key, consumer_secret)
            self.configuration = NeoUtility(
                # consumer_key=consumer_key, consumer_secret=consumer_secret,
                host=environment
            )
            self.api_client = ApiClient(self.configuration)
            # try:
            #     session_init = neo_api_client.LoginAPI(self.api_client).session_init()
            #     print(json.dumps({"data": session_init}))
            # except ApiException as ex:
            #     error = ex
        else:
            # access_token was provided.
            self.configuration = NeoUtility(access_token=access_token, host=environment)
            self.api_client = ApiClient(self.configuration)

        self.NeoWebSocket = None
        self.configuration.neo_fin_key = neo_fin_key
        self.configuration.consumer_key = consumer_key

    def place_order(
        self,
        exchange_segment: str,
        product: str,
        price: str,
        order_type: str,
        quantity: str,
        validity: str,
        trading_symbol: str,
        transaction_type: str,
        amo: str = "NO",
        disclosed_quantity: str = "0",
        trigger_price: str | None = "0",
    ) -> dict[str, Any]:
        """
        Places an order on the specified exchange segment and product, for a given trading symbol, transaction type,
        order type, quantity, and price.

        Parameters:
        exchange_segment (str): The exchange segment (e.g. "NSECM", "BSECM", "NSEFO", etc.)
        product (str): The product type (e.g. "CNC", "MIS", "NRML", etc.)
        price (float): The price of the order
        order_type (str): The order type (e.g. "LIMIT", "MARKET", etc.)
        quantity (int): The quantity of the order
        validity (str): The validity of the order (e.g. "DAY", "IOC", etc.)
        trading_symbol (str): The trading symbol of the stock
        transaction_type (str): The transaction type (e.g. "BUY", "SELL", etc.)
        amo (str, optional): Flag to indicate whether it is an AMO order. Defaults to "NO".
        disclosed_quantity (str, optional): Disclosed quantity for the order. Defaults to "0".
        trigger_price (str, optional): Trigger price for Stop Loss orders. Defaults to "0".

        Note:
        Market protection ("mp") is always sent as "0" — it is not caller-configurable.

        Returns:
        Success/Failure Response from the API

        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                req_data_validation.place_order_validation(
                    exchange_segment,
                    product,
                    price,
                    order_type,
                    quantity,
                    validity,
                    trading_symbol,
                    transaction_type,
                )

                exchange_segment = settings.exchange_segment[exchange_segment]
                product = settings.product[product]
                order_type = settings.order_type[order_type]
                # trigger_price ("tp") is required by the REST API even for
                # order types that ignore it (L/MKT) — it just doesn't matter
                # what the value is. Default it to "0" so callers don't have
                # to pass it for these order types.
                if order_type in settings.NO_TRIGGER_ORDER_TYPES and trigger_price is None:
                    trigger_price = "0"
                place_order = OrderAPI(self.api_client).order_placing(
                    exchange_segment=exchange_segment,
                    product=product,
                    price=price,
                    order_type=order_type,
                    quantity=quantity,
                    validity=validity,
                    trading_symbol=trading_symbol,
                    transaction_type=transaction_type,
                    amo=amo,
                    disclosed_quantity=disclosed_quantity,
                    trigger_price=trigger_price,
                )

                return place_order
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def cancel_order(
        self, order_id: str, amo: str = "NO", isVerify: bool = False
    ) -> dict[str, Any]:
        """
        Cancels an order with the given `order_id` using the NEO API.

        The cancel request is always sent straight to the backend — the
        exchange is the source of truth on whether an order (e.g. one that's
        already complete/traded/rejected/cancelled) can still be cancelled.

        Args: order_id (str): The ID of the order to cancel.
        amo (str, optional): Default is "NO" for no amount specified.
        isVerify (bool, optional): Default is False. Retained for backward
            compatibility; has no effect on this method's behavior.

        Raises:
            ValueError: If the `order_id` is not a valid input.
            Exception: If there was an error cancelling the order.

        Returns:
            The Status of given order id.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                req_data_validation.cancel_order_validation(order_id, amo=amo)
                cancel_order = OrderAPI(self.api_client).order_cancelling(
                    order_id=order_id, isVerify=isVerify, amo=amo
                )
                return cancel_order
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def order_report(self, order_id: str | None = None) -> dict[str, Any]:
        """
        Retrieves orders from the order book using the NEO API.

        Args:
            order_id (str, optional): Nest order number. When provided, a single
                order is fetched from ``/quick/user/orders/<order_no>``. When
                omitted, the full order book is returned.

        Raises:
            Exception: If there was an error retrieving the order book.

        Returns:
            Json object of Orders.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                if order_id:
                    return OrderReportAPI(self.api_client).ordered_book_by_id(order_id=order_id)
                order_list = OrderReportAPI(self.api_client).ordered_books()
                return order_list
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def order_history(self, order_id: str) -> dict[str, Any]:
        """
        Retrieves the order history for a given order ID using the NEO API.

        Args:
            order_id (str): A string representing the order ID to retrieve the history for.

        Raises:
            Exception: If there was an error retrieving the order history.

        Returns:
            Json object with the give order_id.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                req_data_validation.order_history_validation(order_id)
                history_list = OrderHistoryAPI(self.api_client).ordered_history(order_id=order_id)
                return history_list
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def trade_report(self) -> dict[str, Any]:
        """
        Retrieves the full list of trades using the NEO API.

        Raises:
            Exception: If there was an error retrieving the trade report.

        Returns:
            Json object of all trades.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                return TradeReportAPI(self.api_client).trading_report()
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def modify_order(
        self,
        order_id: str,
        price: str,
        order_type: str,
        quantity: str,
        validity: str,
        trigger_price: str | None = "0",
        disclosed_quantity: str = "0",
        amo: str = "NO",
    ) -> dict[str, Any]:
        """
        Modify an existing order with new values for its parameters.

        Args:
            amo: (str, optional): Default sets to NO. Override with 'YES' if you want to pass amo
            order_id (int): The unique identifier of the order to be modified.
            price (float): The new price for the order.
            order_type (str): The new order type for the order.
            quantity (int): The new quantity of the order.
            validity (str): The new validity for the order.
            trigger_price (float, optional): The new trigger price for the order. Defaults to "0".
            disclosed_quantity (str, optional): The new disclosed quantity for the order. Defaults to "0".

        The modify request is always sent straight to the backend — the
        exchange is the source of truth on whether an order (e.g. one that's
        already complete/traded/rejected/cancelled) can still be modified.
        The raw OMS acknowledgement is returned as-is; confirm the final state
        via the order feed or order history.

        Note:
        Market protection ("mp") is always sent as "0" — it is not caller-configurable.

        Returns:
            The Status of the Given Order ID modification
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            # Validate mandatory inputs up-front (before any value mapping) so
            # blank/invalid values are rejected with a clear message.
            try:
                req_data_validation.modify_order_validation(
                    order_id=order_id,
                    price=price,
                    order_type=order_type,
                    quantity=quantity,
                    validity=validity,
                    trigger_price=trigger_price,
                    disclosed_quantity=disclosed_quantity,
                    amo=amo,
                )
            except Exception as e:
                return {"Error": e}

            # order_type is mandatory and already validated above, so it's safe
            # to canonicalize here. trigger_price ("tp") is required by the
            # REST API even for order types that ignore it (L/MKT) — default
            # it to "0" so callers don't have to pass it.
            order_type = settings.order_type[order_type]
            if order_type in settings.NO_TRIGGER_ORDER_TYPES and trigger_price is None:
                trigger_price = "0"

            try:
                return ModifyOrder(self.api_client).quick_modification(
                    order_id=order_id,
                    price=price,
                    order_type=order_type,
                    quantity=quantity,
                    validity=validity,
                    trigger_price=trigger_price,
                    disclosed_quantity=disclosed_quantity,
                    amo=amo,
                )
            except Exception:
                return {"Error": "Exception has been occurred while connecting to API"}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def positions(self) -> dict[str, Any]:
        """
        Retrieves a list of positions using the NEO API.

        Raises:
                Exception: If there was an error retrieving the positions.

        Returns:
                A list of positions.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                position_list = PositionsAPI(self.api_client).position_init()
                return position_list
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def holdings(self) -> dict[str, Any]:
        """
        Retrieves the current holdings for the portfolio using the NEO API.

        Raises:
             Exception: If there was an error retrieving the holdings.

        Returns:
             A list of portfolio holding objects.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                portfolio_list = PortfolioAPI(self.api_client).portfolio_holdings()
                return portfolio_list
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def margin_required(
        self,
        exchange_segment: str,
        price: str,
        order_type: str,
        product: str,
        quantity: str,
        instrument_token: str,
        transaction_type: str,
        trigger_price: str | None = None,
        broker_name: str = "KOTAK",
        branch_id: str = "ONLINE",
        stop_loss_type: str | None = None,
        stop_loss_value: str | None = None,
        square_off_type: str | None = None,
        square_off_value: str | None = None,
        trailing_stop_loss: str | None = None,
        trailing_sl_value: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculates the margin required for a given trade using the NEO API.

        Args:
            exchange_segment (str): Allowed values (exact match only, aliases are not accepted): nse_cm, bse_cm, nse_fo, bse_fo, mcx_fo.
            price (float): The price at which to execute the trade. Zero or a positive value.
            order_type (str): Allowed values (exact match only, aliases are not accepted): L, MKT, SL, SL-M.
            product (str): Allowed values (exact match only, aliases are not accepted): CNC, NRML, MIS, MTF.
            quantity (float): The quantity to trade. Must be a non-zero positive value.
            instrument_token (int): The instrument token (pSymbol) of the stock to trade. Must be a valid positive integer token.
            transaction_type (str): Allowed values: B, S.
            trigger_price (float, optional): The trigger price for the trade.
            broker_name (str, optional): The name of the broker to use. Defaults to "KOTAK". Mandatory, non-blank.
            branch_id (str, optional): The ID of the branch to use. Defaults to "ONLINE". Mandatory, non-blank.
            stop_loss_type (str, optional): The type of stop loss to use.
            stop_loss_value (float, optional): The value for the stop loss.
            square_off_type (str, optional): The type of square off to use.
            square_off_value (float, optional): The value for the square off.
            trailing_stop_loss (str, optional): The type of trailing stop loss to use.
            trailing_sl_value (float, optional): The value for the trailing stop loss.

        Raises:
             Exception: If there was an error calculating the margin.

        Returns:
             The calculated margin required for the trade.

        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                req_data_validation.margin_validation(
                    exchange_segment,
                    price,
                    order_type,
                    product,
                    quantity,
                    instrument_token,
                    transaction_type,
                    broker_name=broker_name,
                    branch_id=branch_id,
                    trigger_price=trigger_price,
                )

                exchange_segment = settings.exchange_segment[exchange_segment]
                product = settings.product[product]
                order_type = settings.order_type[order_type]
                margin_required = MarginAPI(self.api_client).margin_init(
                    exchange_segment=exchange_segment,
                    price=price,
                    order_type=order_type,
                    product=product,
                    quantity=quantity,
                    instrument_token=instrument_token,
                    transaction_type=transaction_type,
                    trigger_price=trigger_price,
                    broker_name=broker_name,
                    branch_id=branch_id,
                    stop_loss_type=stop_loss_type,
                    stop_loss_value=stop_loss_value,
                    square_off_type=square_off_type,
                    square_off_value=square_off_value,
                    trailing_stop_loss=trailing_stop_loss,
                    trailing_sl_value=trailing_sl_value,
                )
                return margin_required
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def scrip_master(self, exchange_segment: str | None = None) -> dict[str, Any]:
        """
        Retrieves the list of scrips available in the given exchange segment using the NEO API.

        Unlike most trading/portfolio methods, this does not require a completed
        2FA (TOTP) session — only `consumer_key` is required, since the
        underlying API authenticates via the `Authorization` header alone.

        Args:
            exchange_segment (str): A string representing the exchange segment to retrieve the list of scrips from.


        Raises:
            Exception: If there was an error retrieving the list of scrips.

        Returns:
            A list of scrips available in the given exchange segment.
        """
        try:
            scrip_list = ScripMasterAPI(self.api_client).scrip_master_init(
                exchange_segment=exchange_segment
            )
            return scrip_list
        except Exception:
            return {"Error": "Exchange Segment is not available"}

    def limits(self) -> dict[str, Any]:
        """
        Retrieves the limits across all segments, exchanges, and products
        using the NEO API.

        Raises:
            Exception: If there was an error retrieving the limits.

        Returns:
            A list of limits across all segments, exchanges, and products.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                limits_list = LimitsAPI(self.api_client).limit_init()
                return limits_list
            except Exception as e:
                return {"Error": e, "message": "Exchange Segment is not available"}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def search_scrip(
        self,
        exchange_segment: str = "",
        symbol: str = "",
        expiry: str | None = None,
        option_type: str | None = None,
        strike_price: str | None = None,
        ignore_50multiple: bool = True,
    ) -> dict[str, Any]:
        """
        Search for a scrip based on the given parameters.

        Args:
            exchange_segment (str): The exchange segment to search in. Mandatory — if
                omitted or blank, returns a client-side validation error (see below)
                rather than raising, so it can be called by keyword with any subset
                of the other parameters without a TypeError.
            symbol (str): The symbol to search for. This argument is optional.
            expiry (str): The expiry date to search for, in the format YYYYMM. This argument is optional.
            option_type (str): The option type to search for — "CE", "PE", or "FUT" for
                futures contracts (mapped internally to the scrip-master's "XX" value,
                since futures rows don't carry "CE"/"PE"). Comma-separated for multiple,
                e.g. "CE,PE". This argument is optional.
            strike_price (str): The strike price to search for. This argument is optional.
            ignore_50multiple (bool): Whether to ignore strike prices that are not multiples of 50. This argument is optional.

        Returns:
            dict: A dictionary containing information about the scrip. If there was an error, the dictionary will contain an "error"
            key with a list of error messages.

        Note:
            Unlike most trading/portfolio methods, this does not require a
            completed 2FA (TOTP) session — only `consumer_key` is required,
            since the underlying API authenticates via the `Authorization`
            header alone.
        """
        if not exchange_segment:
            error = {
                "error": [
                    {
                        "code": "10300",
                        "message": "Validation Errors! Exchange Segment is Mandate to proceed "
                        "further",
                    }
                ]
            }
            return error
        try:
            exchange_segment = settings.exchange_segment[exchange_segment]
            symbol = str(symbol).lower()
            scrip_list = ScripSearch(self.api_client).scrip_search(
                exchange_segment=exchange_segment,
                symbol=symbol,
                expiry=expiry,
                option_type=option_type,
                strike_price=strike_price,
                ignore_50multiple=ignore_50multiple,
            )
            return scrip_list
        except Exception as e:
            return {"Error": e, "message": "Exchange Segment is not available"}

    # ------------------------------------------------------------------
    # Legacy WebSocket API (removed in 2.2.0)
    #
    # The callback-based HSWebSocket/NeoWebSocket implementation has been
    # removed in favour of the modern async/await SFeed WebSocket client.
    # The methods below are retained as stubs so that existing integrations
    # fail with a clear, actionable message instead of an AttributeError.
    #
    # Migrate to:
    #     from neo_api_client.websocket.feed import SFeedWebSocket, WsToken
    #
    #     async with client.create_websocket() as ws:
    #         await ws.subscribe_scrips([WsToken("nse_cm", "11536")])
    #         async for message in ws:
    #             print(message)
    # ------------------------------------------------------------------

    _LEGACY_WS_MESSAGE = (
        "The callback-based WebSocket (subscribe/un_subscribe/subscribe_to_orderfeed) "
        "has been removed in 2.2.0. Use the async SFeed WebSocket instead: "
        "`client.create_websocket()` (see neo_api_client.websocket.feed.SFeedWebSocket)."
    )

    def subscribe(
        self, instrument_tokens: list[dict[str, str]], isIndex: bool = False, isDepth: bool = False
    ) -> NoReturn:
        """
        Removed in 2.2.0. Use :meth:`create_websocket` (SFeed WebSocket) instead.

        Raises:
            NotImplementedError: Always. The legacy WebSocket has been removed.
        """
        raise NotImplementedError(self._LEGACY_WS_MESSAGE)

    def un_subscribe(
        self, instrument_tokens: list[dict[str, str]], isIndex: bool = False, isDepth: bool = False
    ) -> NoReturn:
        """
        Removed in 2.2.0. Use :meth:`create_websocket` (SFeed WebSocket) instead.

        Raises:
            NotImplementedError: Always. The legacy WebSocket has been removed.
        """
        raise NotImplementedError(self._LEGACY_WS_MESSAGE)

    def help(self, function_name: str | None = None) -> dict[str, Any] | None:
        class_name = NeoAPI.__name__
        try:
            if function_name is None:
                print(settings.help_functions)
            else:
                function_name = str(function_name).strip()
                if function_name == "socket":
                    function_name = "create_websocket"
                obj = getattr(NeoAPI, function_name, None)
                if obj is None:
                    print(f"{function_name} is not a valid function name.")
                else:
                    sig = inspect.signature(obj)
                    arg_desc = ", ".join([
                        f"{param.name}: {param.annotation}" for param in sig.parameters.values()
                    ])
                    print(f"{class_name}.{function_name}({arg_desc}): {obj.__doc__}")
        except Exception as e:
            return {
                "Error": "Some Exception while connecting to help, Try after some time!",
                "message": e,
            }
        return None

    def logout(self) -> dict[str, Any]:
        """
        Logs out the user from the NEO API.

        Raises:
            Exception: If there was an error logging out.

        Returns:
            None.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                # log_off = LogoutAPI(self.api_client).logging_out()
                self.configuration.bearer_token = None
                self.configuration.edit_sid = None
                self.configuration.edit_token = None
                return {"State": "OK", "message": "You have been successfully logged out"}

            except Exception:
                return {
                    "State": "NOT_OK",
                    "message": "Some Exception with the Logout Functionality",
                }
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def whatsmyip(self) -> dict[str, Any]:
        """
        Retrieves the client's outbound IP address as seen by the NEO backend.

        This is the IP the server observes for your requests, useful for
        confirming which IP would need to be whitelisted for IP-restricted
        environments.

        Raises:
            Exception: If there was an error fetching the client IP.

        Returns:
            dict: Response containing the client IP and server time, e.g.
            {"data": [{"ip": "...", "time": "..."}], "stCode": 1000, "status": "success"}
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                return ClientIpAPI(self.api_client).whatsmyip()
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def subscribe_to_orderfeed(self) -> NoReturn:
        """
        Removed in 2.2.0. Use :meth:`create_websocket` (SFeed WebSocket) instead.

        Raises:
            NotImplementedError: Always. The legacy WebSocket has been removed.
        """
        raise NotImplementedError(self._LEGACY_WS_MESSAGE)

    def totp_login(
        self,
        mobile_number: str | None = None,
        ucc: str | None = None,
        totp: str | None = None,
    ) -> dict[str, Any]:
        """
        Step 1: Login using TOTP to generate a view token (read-only access).

        Prerequisites:
            - Register for TOTP at https://www.kotaksecurities.com/platform/kotak-neo-trade-api/
            - Set up authenticator app (Google Authenticator, Authy, etc.)
            - Have your consumer_key configured during NeoAPI initialization

        Args:
            mobile_number (str): Your registered mobile number with country code.
                Example: "+919876543210"
            ucc (str): Unique Client Code - find in NEO app under Profile section.
                Example: "ABC123"
            totp (str): 6-digit Time-based One-Time Password from authenticator app.
                This code changes every 30 seconds.
                Example: "123456"

        Returns:
            dict: Response containing view token, session ID, and user details.
            {
                "data": {
                    "token": "eyJhbGc...",  # View token (read-only)
                    "sid": "session-id",
                    "ucc": "ABC123",
                    "greetingName": "User Name",
                    "kId": "PAN_NUMBER",
                    "kType": "View",  # Indicates view-only access
                    "status": "success",
                    ...
                }
            }

        Example:
            ```python
            response = client.totp_login(
                mobile_number="+919876543210",
                ucc="ABC123",
                totp="123456"  # From authenticator app
            )
            ```

        Note:
            After totp_login, you must call totp_validate(mpin) to get trading access.
            Blank/missing input is rejected client-side (no network call),
            using the same error shape the backend itself returns for this
            case, e.g.:
            {"error": [{"code": "400", "message": "Missing required field 'MobileNumber'"}]}
        """
        if not mobile_number:
            return {"error": [{"code": "400", "message": "Missing required field 'MobileNumber'"}]}
        if not ucc:
            return {"error": [{"code": "400", "message": "Missing required field 'Ucc'"}]}
        if not totp:
            return {"error": [{"code": "400", "message": "Missing required field 'Totp'"}]}

        totp_login = TotpAPI(self.api_client).totp_login(
            mobile_number=mobile_number, ucc=ucc, totp=totp
        )
        return totp_login

    def totp_validate(self, mpin: str | None = None) -> dict[str, Any]:
        """
        Step 2: Validate MPIN to upgrade from view token to trade token (full trading access).

        This method must be called after totp_login() to complete the authentication flow
        and obtain trading permissions.

        Args:
            mpin (str): Your 6-digit Mobile PIN for trading authorization.
                This is the MPIN you set up for your Kotak NEO trading account.
                Example: "123456"

        Returns:
            dict: Response containing trade token with full access permissions.
            {
                "data": {
                    "token": "eyJhbGc...",  # Trade token (full access)
                    "sid": "session-id",
                    "rid": "request-id",
                    "baseUrl": "api-url",
                    "dataCenter": "gdc",
                    "kType": "Trade",  # Indicates trading access enabled
                    "status": "success",
                    ...
                }
            }

        Example:
            ```python
            # After successful totp_login()
            response = client.totp_validate(mpin="123456")

            # Now you have full trading access
            # You can place orders, modify positions, etc.
            ```

        Updates:
            - Sets edit_token for trading operations
            - Sets edit_sid, edit_rid for session management
            - Configures base_url and data_center for API routing

        Note:
            Both totp_login() and totp_validate() must succeed before you can perform
            trading operations like placing orders.
            Blank/missing mpin is rejected client-side (no network call),
            using the same error shape the backend itself returns for this
            case:
            {"error": [{"code": "400", "message": "Missing required field 'Mpin'"}]}
        """
        if not mpin:
            return {"error": [{"code": "400", "message": "Missing required field 'Mpin'"}]}

        totp_validate = TotpAPI(self.api_client).totp_validate(mpin=mpin)
        return totp_validate

    def create_websocket(self, url: str | None = None, **kwargs: Any) -> SFeedWebSocket:
        """
        Create a modern async/await SFeed WebSocket client.

        This method provides a convenient way to create a SFeedWebSocket instance
        with authentication credentials already configured from the current session.

        The SFeed native_batch auth frame uses ``user``/``auth`` credentials.
        By default these are derived from the current session (``user`` = edit_sid,
        ``auth`` = edit_token); override via kwargs (``user=``, ``auth=``, ``source=``)
        if your feed credentials differ.

        Args:
            url: Optional WebSocket URL override (defaults to production SFeed URL)
            **kwargs: Additional arguments passed to SFeedWebSocket constructor
                (e.g., user, auth, source, sdk_version, sdk_date, reconnect_delay,
                max_reconnect_attempts, max_connect_retries, ping_interval)

        Returns:
            SFeedWebSocket: Configured WebSocket client ready to connect

        Raises:
            ValueError: If user is not authenticated (no edit_token or edit_sid)

        Example:
            ```python
            import asyncio
            from neo_api_client import NeoAPI
            from neo_api_client.websocket.feed import WsToken

            async def main():
                # Login
                client = NeoAPI(consumer_key="...", environment="prod")
                client.totp_login(mobile_number="+91...", ucc="...", totp="...")
                client.totp_validate(mpin="...")

                # Create and use WebSocket
                async with client.create_websocket() as ws:
                    await ws.subscribe_scrips([
                        WsToken("nse_cm", "1333"),  # RELIANCE
                    ])

                    async for message in ws:
                        print(f"LTP: {message.last_traded_price}")

            asyncio.run(main())
            ```

        Note:
            Requires Python 3.10+ and async/await support.
            Make sure to call totp_login() and totp_validate() before creating WebSocket.
        """
        from neo_api_client.websocket.feed import SFeedWebSocket

        if not self.configuration.edit_token or not self.configuration.edit_sid:
            raise ValueError(
                "Authentication required. Please call totp_login() and totp_validate() first."
            )

        # Prefer an explicit url, then the data-center-specific URL resolved
        # by resolve_dynamic_urls() during totp_validate(), then the feedUrl
        # from that same totp_validate() response, then let SFeedWebSocket
        # fall back to its hardcoded default (SFEED_WEBSOCKET_URL).
        if url is not None:
            kwargs["url"] = url
        elif self.configuration.sfeed_websocket_url:
            kwargs["url"] = self.configuration.sfeed_websocket_url
        elif self.configuration.feed_url:
            kwargs["url"] = self.configuration.feed_url

        if "ucc" not in kwargs and "user" not in kwargs:
            kwargs["ucc"] = self.configuration.ucc

        return SFeedWebSocket(
            access_token=self.configuration.edit_token,
            sid=self.configuration.edit_sid,
            **kwargs,
        )

    def create_order_feed(self, **kwargs: Any) -> OrderFeedWebSocket:
        """
        Create an async/await Order & Position streaming WebSocket client.

        Streams real-time order-lifecycle events and live position updates over
        ``wss://<baseurl>/realtime``, where ``<baseurl>`` is the host returned by
        ``totp_validate`` (stored as ``configuration.base_url``).

        Args:
            **kwargs: Additional arguments passed to OrderFeedWebSocket
                (e.g., source, reconnect_delay, max_reconnect_attempts,
                max_connect_retries, ping_interval).

        Returns:
            OrderFeedWebSocket: Configured client ready to connect.

        Raises:
            ValueError: If not authenticated (no edit_token/edit_sid) or the
                base URL is unavailable (totp_validate not completed).

        Example:
            ```python
            import asyncio
            from neo_api_client import NeoAPI

            async def main():
                client = NeoAPI(consumer_key="...", environment="prod")
                client.totp_login(mobile_number="+91...", ucc="...", totp="...")
                client.totp_validate(mpin="...")

                async with client.create_order_feed() as feed:
                    async for message in feed:
                        print(message)

            asyncio.run(main())
            ```
        """
        from neo_api_client.websocket.orderfeed import OrderFeedWebSocket

        if not self.configuration.edit_token or not self.configuration.edit_sid:
            raise ValueError(
                "Authentication required. Please call totp_login() and totp_validate() first."
            )

        # Prefer an explicit url kwarg, then the data-center-specific URL
        # resolved by resolve_dynamic_urls() during totp_validate(), then the
        # rtUrl from that same totp_validate() response. If none of those are
        # available, OrderFeedWebSocket falls back to base_url (from
        # totp_validate()) itself; if even that's missing, fall back to the
        # hardcoded ORDER_FEED_URL_* default for this data center.
        if "url" not in kwargs and self.configuration.order_feed_url:
            kwargs["url"] = self.configuration.order_feed_url
        elif "url" not in kwargs and self.configuration.rt_url:
            kwargs["url"] = self.configuration.rt_url

        if "url" not in kwargs and not self.configuration.base_url:
            fallback_url = _ORDER_FEED_URL_BY_DATA_CENTER.get(self.configuration.data_center)
            if not fallback_url:
                raise ValueError(
                    "Order-feed base URL is unavailable. Complete totp_validate() first."
                )
            kwargs["url"] = fallback_url

        return OrderFeedWebSocket(
            base_url=self.configuration.base_url,
            auth=self.configuration.edit_token,
            sid=self.configuration.edit_sid,
            **kwargs,
        )

    def quotes(
        self, instrument_tokens: list[dict[str, str]] | None = None, quote_type: str | None = None
    ) -> dict[str, Any]:
        """
        Retrieves quotes for the given instrument tokens.

        Args:
            instrument_tokens (List): A JSON-encoded list of instrument tokens to subscribe to.
            quote_type (str): The type of quote to subscribe to.

        Returns:
            JSON-encoded list of Quotes information

        Raises:
            ValueError: If the instrument tokens are not provided.
        """
        if not instrument_tokens:
            error = {"error": [{"message": "Validation Errors! instrument_tokens are missing"}]}
            return error
        quotes_response = QuotesAPI(self.api_client).get_quotes(
            instrument_tokens=instrument_tokens, quote_type=quote_type
        )
        return quotes_response
