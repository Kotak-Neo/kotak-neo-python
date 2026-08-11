#############################################################################
#                        SFeed WebSocket URLs
#############################################################################
SFEED_WEBSOCKET_URL = "wss://sfeed.kotaksecurities.com/wsfeed"

#############################################################################
#                               UAT BASE URLs
#############################################################################
UAT_BASE_URL = "https://d-mis.kotaksecurities.com"
PROD_BASE_URL = "https://mis.kotaksecurities.com"
PROD_BASE_URL_ADC = "https://cis.kotaksecurities.com"

#############################################################################
#                  SESSION URLs (for TOTP login/validate only)
#############################################################################
SESSION_UAT_BASE_URL = "https://d-mis.kotaksecurities.com"
SESSION_PROD_BASE_URL = "https://mis.kotaksecurities.com"
SESSION_PROD_BASE_URL_ADC = "https://mis.kotaksecurities.com"

#############################################################################
#                               ORDER_FEED  URL
#############################################################################
ORDER_FEED_URL = "wss://mis.kotaksecurities.com/realtime"
ORDER_FEED_URL_ADC = "wss://cis.kotaksecurities.com/realtime"
ORDER_FEED_URL_E21 = "wss://e21.kotaksecurities.com/realtime"
ORDER_FEED_URL_E22 = "wss://e22.kotaksecurities.com/realtime"
ORDER_FEED_URL_E41 = "wss://e41.kotaksecurities.com/realtime"
ORDER_FEED_URL_E43 = "wss://e43.kotaksecurities.com/realtime"

#############################################################################
#                     DYNAMIC CONFIG SERVICE
#############################################################################
# After totp_validate() learns the account's dataCenter, the SDK queries this
# service for that data center's feed endpoints (e.g. the SFeed websocket
# URL), falling back to the hardcoded SFEED_WEBSOCKET_URL above if the call
# fails or the data center has no entry.
CONFIG_SERVICE_URL_UAT = "https://qapi.kotaksecurities.online/5config/config"
# TODO: replace with the real prod config-service URL once available from the
# Solution Architect. Pointed at the UAT URL for now (with environment=uat
# below) so the prod code path can be exercised end-to-end ahead of that.
CONFIG_SERVICE_URL_PROD = CONFIG_SERVICE_URL_UAT

# appVersion isn't validated by the config service, so the SDK sends its own
# package version (see neo_api_client.__version__) rather than a fixed value.
CONFIG_SERVICE_PLATFORM = "api"
CONFIG_SERVICE_ENVIRONMENT_UAT = "qa"
# TODO: confirm the real prod "environment" value with the Solution
# Architect; "uat" is a placeholder matching CONFIG_SERVICE_URL_PROD above.
CONFIG_SERVICE_ENVIRONMENT_PROD = "uat"
