import inspect

from neo_api_client import req_data_validation, settings
from neo_api_client.api_client import ApiClient
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
from neo_api_client.websocket.NeoWebSocket import NeoWebSocket


class NeoAPI:
    """
    A class representing the NeoAPI, which is a client API for the Neo banking platform.

    The `NeoAPI` class provides methods to initialize the API client, log in to the platform, generate OTP, and perform 2FA authentication.

    Attributes:
        environment (str): The environment for the API client.
        configuration (neo_api_client.Configuration): The configuration for the API client.
        consumer_key (str): The consumer key for the API client.
        consumer_secret (str): The consumer secret for the API client.
        username (str): The username for the API client.
        password (str): The password for the API client.
        api_client (ApiClient): The API client instance.

    Methods:
        __init__(consumer_key=None, consumer_secret=None, host='uat', username=None, password=None):
            Initializes the `NeoAPI` instance with the given consumer key, consumer secret, host, username, and password.
            Validates the configuration and creates an API client instance.

        login(mobileNumber, password):
            Logs in to the platform using the given mobile number and password.
            Sets the view token, SID, and server ID in the configuration.

        generateOTP():
            Generates an OTP for 2FA authentication.

        session_2fa(OTP):
            Performs 2FA authentication using the given OTP.
            Sets the edit token, SID, RID, and server ID in the configuration.
    """

    def __init__(self, environment="uat", access_token=None, neo_fin_key=None, consumer_key=None):
        """
        Initializes the class and sets up the necessary configurations for the API client.

        Parameters:
        environment (str): The environment has to pass by user to connect 'UAT' or 'PROD'.
        access_token (str, optional): The access token used for authentication. Defaults to None.
        consumer_key (str, optional): The consumer key used for authentication. Defaults to None.
        consumer_secret (str, optional): The consumer secret used for authentication. Defaults to None.
        neo_fin_key (str, optional): Finkey for tracking purpose

        Updates:
        self.on_message: sets the callback function for incoming messages for Websocket.
        self.on_error: sets the callback function for errors for Websocket.
        self.on_close: sets the callback function for connection close events for Websocket.
        self.on_open: sets the callback function for connection open events for Websocket.

        Raises:
        ApiException: if the session initiation fails.
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
        elif access_token:
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
                req_data_validation.cancel_order_validation(order_id)
                cancel_order = OrderAPI(self.api_client).order_cancelling(
                    order_id=order_id, isVerify=isVerify, amo=amo
                )
                return cancel_order
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def cancel_cover_order(self, order_id, amo="NO", isVerify=False):
        """
        Cancels a cover order with the given `order_id` using the NEO API.

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
                req_data_validation.cancel_order_validation(order_id)
                cancel_order = OrderAPI(self.api_client).cover_order_cancelling(
                    order_id=order_id, isVerify=isVerify, amo=amo
                )
                return cancel_order
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def cancel_bracket_order(self, order_id, amo="NO", isVerify=False):
        """
        Cancels a bracket order with the given `order_id` using the NEO API.

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
                req_data_validation.cancel_order_validation(order_id)
                cancel_order = OrderAPI(self.api_client).bracket_order_cancelling(
                    order_id=order_id, isVerify=isVerify, amo=amo
                )
                return cancel_order
            except Exception as e:
                return {"Error": e}
        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def order_report(self):
        """
        Retrieves a list of orders in the order book using the NEO API.

        Raises:
            Exception: If there was an error retrieving the order book.

        Returns:
            Json object of Orders.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            try:
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

        Raises:
            ValueError: If order ID is not provided.

        Returns:
            The Status of the Given Order ID modification
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
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

    def __on_open(self):
        if self.on_open:
            self.on_open("The Session has been Opened!")

    def __on_close(self):
        # print("[Socket]: Disconnected Demo Func !")
        if self.on_close:
            self.on_close("The Session has been Closed!")

    def __on_error(self, error):
        # print("[Socket]: Error !")
        if self.on_error:
            self.on_error(error)

    def __on_message(self, message):
        # print('[NEO_API]: "In-side NeoAPI Class')
        if self.on_message:
            self.on_message(message)

    def check_callbacks(self):
        show_warning = (
            not self.on_close or not self.on_open or not self.on_message or not self.on_error
        )
        if show_warning:
            warnings = "Warning!\n"
            if self.on_message is None:
                warnings += "on_message callback is not Set\n"
            if self.on_error is None:
                warnings += "on_error callback is not Set\n"
            if self.on_close is None:
                warnings += "on_close callback is not Set\n"
            if self.on_open is None:
                warnings += "on_open callback is not Set\n"

            warnings += "It is recommended to set callbacks to handle your own logic on events."
            print(warnings)

    def set_neowebsocket_callbacks(self):
        if self.NeoWebSocket is not None:
            self.NeoWebSocket.on_message = self.__on_message
            self.NeoWebSocket.on_error = self.__on_error
            self.NeoWebSocket.on_open = self.__on_open
            self.NeoWebSocket.on_close = self.__on_close

    def subscribe(self, instrument_tokens, isIndex=False, isDepth=False):
        """
        Subscribe to live feeds for the given instrument tokens.

        Args:
            instrument_tokens (List): A JSON-encoded list of instrument tokens to subscribe to.
            isIndex (bool): Whether the instrument is an index. Default is False.
            isDepth (bool): Whether to subscribe to depth data. Default is False.

        Raises:
            ValueError: If the login flow is not completed.

        Returns:
            Live Feed from the socket

        The function establishes a WebSocket connection to the trading platform and subscribes to live feeds for the specified instrument tokens. When a new feed is received, the function's internal callback functions are called with the feed data as their arguments. If an error occurs, the on_error function is called with the error message as its argument.
        """

        if self.configuration.edit_token and self.configuration.edit_sid:
            if not self.NeoWebSocket:
                self.check_callbacks()
                self.NeoWebSocket = NeoWebSocket(
                    self.configuration.edit_sid,
                    self.configuration.edit_token,
                    self.configuration.serverId,
                    data_center=None,
                )
                self.set_neowebsocket_callbacks()
            self.NeoWebSocket.get_live_feed(
                instrument_tokens=instrument_tokens, isIndex=isIndex, isDepth=isDepth
            )
        else:
            print("Please complete the Login Flow to Subscribe the Scrips")

    def un_subscribe(self, instrument_tokens, isIndex=False, isDepth=False):
        """
        Unsubscribe the live feeds for the subscribed instrument tokens.

        Args:
            instrument_tokens (List): A JSON-encoded list of instrument tokens.
            isIndex (bool): Whether the instrument is an index. Default is False.
            isDepth (bool): Whether to subscribe to depth data. Default is False.

        Raises:
            ValueError: If the login flow is not completed.

        Returns:
            Message that its successfully unsubscribed
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            if not self.NeoWebSocket:
                self.NeoWebSocket = NeoWebSocket(
                    self.configuration.edit_sid,
                    self.configuration.edit_token,
                    self.configuration.serverId,
                    data_center=None,
                )

            self.set_neowebsocket_callbacks()
            self.NeoWebSocket.un_subscribe_list(
                instrument_tokens=instrument_tokens, isIndex=isIndex, isDepth=isDepth
            )
            print("The Data has been Un-Subscribed")
        else:
            raise ValueError("Please complete the Login Flow to Un_Subscribe the Scrips")

    def help(self, function_name=None):
        class_name = NeoAPI.__name__
        try:
            if function_name is None:
                print(settings.help_functions)
            else:
                function_name = str(function_name).strip()
                if function_name == "socket":
                    function_name = "subscribe"
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

    def subscribe_to_orderfeed(self):
        """
        Subscribe To OrderFeed

        Raises:
            Exception: If the user hasn't completes his 2FA.

        Returns:
            Order Feed information.
        """
        if self.configuration.edit_token and self.configuration.edit_sid:
            self.check_callbacks()
            if not self.NeoWebSocket:
                self.NeoWebSocket = NeoWebSocket(
                    self.configuration.edit_sid,
                    self.configuration.edit_token,
                    self.configuration.serverId,
                    self.configuration.data_center,
                )
            self.set_neowebsocket_callbacks()
            self.NeoWebSocket.get_order_feed()

        else:
            return {"Error Message": "Complete the 2fa process before accessing this application"}

    def totp_login(self, mobile_number=None, ucc=None, totp=None):
        """
        Logs in to the system by generating a view token using mobile_number, totp and ucc

        Args:
            mobile_number (str): Registered mobile number
            ucc (str): Unique Client Code which you will find in mobile application/website under profile section
            totp (str): The 6 digit code generated on the authenticator app

        Returns:
            {
                "data": {"token": "", "sid": "", "rid": "", "hsServerId": "", "isUserPwdExpired": , "ucc": "",
                    "greetingName": "", "isTrialAccount": , "dataCenter": "", "searchAPIKey": "",
                    "derivativesRiskDisclosure": "", "mfAccess": 1, "dataCenterMap": null, "dormancyStatus": "",
                    "asbaStatus": "", "clientType": "", "isNRI": false, "kId": "", "kType": "", "status": "",
                    "incRange": 0, "incUpdFlag": "", "clientGroup": ""}
            }

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
        Establishes a session with the API using the generated view token and mpin.

        Parameters:
        mpin (str): The 6 digit pin

        Returns: {
            "data": {"token": "", "sid": "", "rid": "", "hsServerId": "", "isUserPwdExpired": false, "ucc": "",
                "greetingName": "", "isTrialAccount": false, "dataCenter": "gdc", "searchAPIKey": "",
                "derivativesRiskDisclosure": "", "mfAccess": 1, "dataCenterMap": null, "dormancyStatus": "",
                "asbaStatus": "", "clientType": "", "isNRI": false, "kId": "", "kType": "", "status": "",
                "incRange": 0, "incUpdFlag": "", "clientGroup": ""}
        }

        Updates:
        edit_token: sets the edit token obtained from the API response.
        """
        if not mpin:
            error = {"error": [{"message": "Mpin is missing"}]}
            return error

        totp_validate = TotpAPI(self.api_client).totp_validate(mpin=mpin)
        return totp_validate

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
