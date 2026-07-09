import inspect

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
        1. Get consumer_key from NEO app (Invest → Trade API → Generate application)
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

    def __init__(self, consumer_key=None, environment="prod", access_token=None, neo_fin_key=None):
        """
        Initializes the NeoAPI client with authentication credentials.

        Parameters:
            consumer_key (str): **REQUIRED** - Consumer key token from NEO app Trade API card.
                How to get: Login to NEO app/web → Invest tab → Trade API → Generate application → Copy token.
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
        exchange_segment,
        product,
        price,
        order_type,
        quantity,
        validity,
        trading_symbol,
        transaction_type,
        amo="NO",
        disclosed_quantity="0",
        market_protection="0",
        pf="N",
        trigger_price="0",
        tag=None,
        scrip_token=None,
        square_off_type=None,
        stop_loss_type=None,
        stop_loss_value=None,
        square_off_value=None,
        last_traded_price=None,
        trailing_stop_loss=None,
        trailing_sl_value=None,
    ):
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
        market_protection (str, optional): Flag to indicate whether market protection is enabled. Defaults to "0".
        pf (str, optional): Flag to indicate whether the order is a Portfolio order. Defaults to "N".
        trigger_price (str, optional): Trigger price for Stop Loss orders. Defaults to "0".
        tag (str, optional): Optional tag to be added to the order. Defaults to None.

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
                    market_protection=market_protection,
                    pf=pf,
                    trigger_price=trigger_price,
                    tag=tag,
                    scrip_token=scrip_token,
                    square_off_type=square_off_type,
                    stop_loss_type=stop_loss_type,
                    stop_loss_value=stop_loss_value,
                    square_off_value=square_off_value,
                    last_traded_price=last_traded_price,
                    trailing_stop_loss=trailing_stop_loss,
                    trailing_sl_value=trailing_sl_value,
                )

                return place_order
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def cancel_order(self, order_id, amo="NO", isVerify=False):
        """
        Cancels an order with the given `order_id` using the NEO API.

        Args: order_id (str): The ID of the order to cancel.
        amo (str, optional): Default is "NO" for no amount specified.
        isVerify (bool, optional): Whether to verify the cancellation. Default is False.
        "If isVerify is True, we will first check the status of the given order. If the order status is not
         'rejected', 'cancelled', 'traded', or 'completed', we will proceed to cancel the order using the
         cancel_order function. Otherwise, we will display the order status to the user instead."

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

    def order_report(self, order_id=None):
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

    def order_history(self, order_id):
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

    def trade_report(self, order_id=None):
        """
        Retrieves a filtered list of trades using the NEO API.

        Args:
            order_id (str): An optional string representing the order ID to filter trades by. If not provided,
                all trades will be returned.

        Raises:
            Exception: If there was an error retrieving the trade report.

        Returns:
            Json object of all trades/filtered items.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                filtered_trades = TradeReportAPI(self.api_client).trading_report(order_id=order_id)
                return filtered_trades
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def modify_order(
        self,
        order_id,
        price,
        order_type,
        quantity,
        validity,
        instrument_token=None,
        exchange_segment=None,
        product=None,
        trading_symbol=None,
        transaction_type=None,
        trigger_price="0",
        dd="NA",
        market_protection="0",
        disclosed_quantity="0",
        filled_quantity="0",
        amo="NO",
        isVerify=False,
    ):
        """
        There are 2 ways to modify the order one is bypassing all the parameters and another one is
        pass the order_id based on that we will take the values from order book and updated the latest details

        Modify an existing order with new values for its parameters.

        Args:
            amo: (str, optional): Default sets to NO. Override with 'YES' if you want to pass amo
            order_id (int): The unique identifier of the order to be modified.
            price (float): The new price for the order.
            order_type (str): The new order type for the order.
            quantity (int): The new quantity of the order.
            validity (str): The new validity for the order.
            instrument_token (int, optional): The unique identifier of the instrument. Defaults to None.
            exchange_segment (str, optional): The exchange segment of the order. Defaults to None.
            product (str, optional): The product type for the order. Defaults to None.
            trading_symbol (str, optional): The trading symbol of the order. Defaults to None.
            transaction_type (str, optional): The transaction type for the order. Defaults to None.
            trigger_price (float, optional): The new trigger price for the order. Defaults to "0".
            dd (str, optional): The new disclosed quantity for the order. Defaults to "NA".
            market_protection (str, optional): The new market protection for the order. Defaults to "0".
            disclosed_quantity (str, optional): The new disclosed quantity for the order. Defaults to "0".
            filled_quantity (str, optional): The new filled quantity for the order. Defaults to "0".
            isVerify (bool, optional): Defaults to False. A modify request is
                acknowledged asynchronously — the OMS returns ``stat: "Ok"`` when
                it accepts the request, but the exchange may reject it moments
                later (e.g. price outside the allowed band), which only shows up
                afterwards on the order book. When True, the SDK re-reads the
                order book after the modify and returns a failure dict
                (``stat: "Not_Ok"`` with the rejection reason) if the order ended
                up rejected/cancelled. Leaving it False returns the raw OMS
                acknowledgement; confirm the final state via the order feed or
                order history.

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
                    market_protection=market_protection,
                    amo=amo,
                    exchange_segment=exchange_segment,
                )
            except Exception as e:
                return {"Error": e}

            if order_id and instrument_token and exchange_segment and product and trading_symbol:
                exchange_segment = settings.exchange_segment[exchange_segment]
                product = settings.product[product]
                order_type = settings.order_type[order_type]
                try:
                    quick_modify = ModifyOrder(self.api_client).quick_modification(
                        order_id=order_id,
                        price=price,
                        order_type=order_type,
                        quantity=quantity,
                        validity=validity,
                        instrument_token=instrument_token,
                        product=product,
                        exchange_segment=exchange_segment,
                        trading_symbol=trading_symbol,
                        transaction_type=transaction_type,
                        trigger_price=trigger_price,
                        dd=dd,
                        market_protection=market_protection,
                        disclosed_quantity=disclosed_quantity,
                        filled_quantity=filled_quantity,
                        amo=amo,
                        is_verify=isVerify,
                    )
                    return quick_modify
                except Exception:
                    return {"Error": "Exception has been occurred while connecting to API"}
            elif order_id and not instrument_token and not exchange_segment and not trading_symbol:
                try:
                    modify_order = ModifyOrder(self.api_client).modification_with_orderid(
                        order_id=order_id,
                        price=price,
                        order_type=order_type,
                        quantity=quantity,
                        validity=validity,
                        instrument_token=instrument_token,
                        product=product,
                        exchange_segment=exchange_segment,
                        trading_symbol=trading_symbol,
                        transaction_type=transaction_type,
                        trigger_price=trigger_price,
                        dd=dd,
                        market_protection=market_protection,
                        disclosed_quantity=disclosed_quantity,
                        filled_quantity=filled_quantity,
                        amo=amo,
                        is_verify=isVerify,
                    )
                    return modify_order

                except Exception:
                    return {"Error": "Exception has been occurred while connecting to API"}

            else:
                raise ValueError("Order ID is Mandate if we need to proceed further!")
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def positions(self):
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

    def holdings(self):
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
        exchange_segment,
        price,
        order_type,
        product,
        quantity,
        instrument_token,
        transaction_type,
        trigger_price=None,
        broker_name="KOTAK",
        branch_id="ONLINE",
        stop_loss_type=None,
        stop_loss_value=None,
        square_off_type=None,
        square_off_value=None,
        trailing_stop_loss=None,
        trailing_sl_value=None,
    ):
        """
        Calculates the margin required for a given trade using the NEO API.

        Args:
            exchange_segment (str): A string representing the exchange segment for the trade.
            price (float): The price at which to execute the trade.
            order_type (str): A string representing the type of order to place.
            product (str): A string representing the product type for the trade.
            quantity (float): The quantity to trade.
            instrument_token (int): The instrument token of the stock to trade.
            transaction_type (str): A string representing the type of transaction to perform.
            trigger_price (float, optional): The trigger price for the trade.
            broker_name (str, optional): The name of the broker to use. Defaults to "KOTAK".
            branch_id (str, optional): The ID of the branch to use. Defaults to "ONLINE".
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

    def scrip_master(self, exchange_segment=None):
        """
        Retrieves the list of scrips available in the given exchange segment using the NEO API.

        Args:
            exchange_segment (str): A string representing the exchange segment to retrieve the list of scrips from.


        Raises:
            Exception: If there was an error retrieving the list of scrips.

        Returns:
            A list of scrips available in the given exchange segment.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                scrip_list = ScripMasterAPI(self.api_client).scrip_master_init(
                    exchange_segment=exchange_segment
                )
                return scrip_list
            except Exception:
                return {"Error": "Exchange Segment is not available"}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def limits(self, segment="ALL", exchange="ALL", product="ALL"):
        """
        Retrieves the limits available for the given segment, exchange and product using the NEO API.

        Args:
            segment (str): A string representing the segment for which limits are to be retrieved. Default value is "ALL".
            exchange (str): A string representing the exchange for which limits are to be retrieved. Default value is "ALL".
            product (str): A string representing the product for which limits are to be retrieved. Default value is "ALL".

        Raises:
            Exception: If there was an error retrieving the limits.

        Returns:
            A list of limits available for the given segment, exchange and product.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
                req_data_validation.limits_validation(segment, exchange, product)

                limits_list = LimitsAPI(self.api_client).limit_init(
                    segment=segment, exchange=exchange, product=product
                )
                return limits_list
            except Exception as e:
                return {"Error": e, "message": "Exchange Segment is not available"}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def search_scrip(
        self,
        exchange_segment,
        symbol="",
        expiry=None,
        option_type=None,
        strike_price=None,
        ignore_50multiple=True,
    ):
        """
        Search for a scrip based on the given parameters.

        Args:
            exchange_segment (str): The exchange segment to search in. This argument is mandatory.
            symbol (str): The symbol to search for. This argument is optional.
            expiry (str): The expiry date to search for, in the format YYYYMM. This argument is optional.
            option_type (str): The option type to search for (either "CE" or "PE"). This argument is optional.
            strike_price (str): The strike price to search for. This argument is optional.
            ignore_50multiple (bool): Whether to ignore strike prices that are not multiples of 50. This argument is optional.

        Returns:
            dict: A dictionary containing information about the scrip. If there was an error, the dictionary will contain an "error"
            key with a list of error messages.

        """
        if self.configuration.edit_token and self.configuration.edit_sid:
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
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

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

    def subscribe(self, instrument_tokens, isIndex=False, isDepth=False):
        """
        Removed in 2.2.0. Use :meth:`create_websocket` (SFeed WebSocket) instead.

        Raises:
            NotImplementedError: Always. The legacy WebSocket has been removed.
        """
        raise NotImplementedError(self._LEGACY_WS_MESSAGE)

    def un_subscribe(self, instrument_tokens, isIndex=False, isDepth=False):
        """
        Removed in 2.2.0. Use :meth:`create_websocket` (SFeed WebSocket) instead.

        Raises:
            NotImplementedError: Always. The legacy WebSocket has been removed.
        """
        raise NotImplementedError(self._LEGACY_WS_MESSAGE)

    def help(self, function_name=None):
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
                    arg_desc = ", ".join(
                        [f"{param.name}: {param.annotation}" for param in sig.parameters.values()]
                    )
                    print(f"{class_name}.{function_name}({arg_desc}): {obj.__doc__}")
        except Exception as e:
            return {
                "Error": "Some Exception while connecting to help, Try after some time!",
                "message": e,
            }

    def logout(self):
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

    def whatsmyip(self):
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

    def subscribe_to_orderfeed(self):
        """
        Removed in 2.2.0. Use :meth:`create_websocket` (SFeed WebSocket) instead.

        Raises:
            NotImplementedError: Always. The legacy WebSocket has been removed.
        """
        raise NotImplementedError(self._LEGACY_WS_MESSAGE)

    def totp_login(self, mobile_number=None, ucc=None, totp=None):
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
        """
        if not mobile_number or not ucc or not totp:
            error = {"error": [{"message": "Any of Mobile Number, UCC or totp is missing"}]}
            return error
        totp_login = TotpAPI(self.api_client).totp_login(
            mobile_number=mobile_number, ucc=ucc, totp=totp
        )
        return totp_login

    def totp_validate(self, mpin=None):
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
        """
        if not mpin:
            error = {"error": [{"message": "Mpin is missing"}]}
            return error

        totp_validate = TotpAPI(self.api_client).totp_validate(mpin=mpin)
        return totp_validate

    def create_websocket(self, url: str = None, **kwargs):
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
                max_reconnect_attempts, ping_interval)

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

        # Only override the URL when one is explicitly provided, otherwise let
        # SFeedWebSocket fall back to its default (SFEED_WEBSOCKET_URL).
        if url is not None:
            kwargs["url"] = url

        return SFeedWebSocket(
            access_token=self.configuration.edit_token,
            sid=self.configuration.edit_sid,
            **kwargs,
        )

    def create_order_feed(self, **kwargs):
        """
        Create an async/await Order & Position streaming WebSocket client.

        Streams real-time order-lifecycle events and live position updates over
        ``wss://<baseurl>/realtime``, where ``<baseurl>`` is the host returned by
        ``totp_validate`` (stored as ``configuration.base_url``).

        Args:
            **kwargs: Additional arguments passed to OrderFeedWebSocket
                (e.g., source, reconnect_delay, max_reconnect_attempts, ping_interval).

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
        if not self.configuration.base_url:
            raise ValueError("Order-feed base URL is unavailable. Complete totp_validate() first.")

        return OrderFeedWebSocket(
            base_url=self.configuration.base_url,
            auth=self.configuration.edit_token,
            sid=self.configuration.edit_sid,
            **kwargs,
        )

    def quotes(self, instrument_tokens=None, quote_type=None):
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
