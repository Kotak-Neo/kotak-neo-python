from neo_api_client.req_data_validation import validate_configuration


def test_validate_configuration():
    validate_configuration(
        consumer_key="dummy_key",
        consumer_secret="dummy_secret",
    )
