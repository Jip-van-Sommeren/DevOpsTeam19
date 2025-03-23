import json
from unittest.mock import MagicMock, patch

from src.location_methods import lambda_handler, get_locations


def test_lambda_handler_not_found():
    """Test that a request for an unknown resource returns 404."""
    event = {"httpMethod": "GET", "resource": "/unknown"}
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Not Found" in body["message"]


@patch("src.location_methods.get_session")
def test_get_locations_success(mock_get_session):
    """
    Test GET /locations returns a list of locations.
    We simulate two fake location objects and verify that the response
    JSON contains their data.
    """
    # Create two fake location objects.
    fake_loc1 = MagicMock()
    fake_loc1.id = 1
    fake_loc1.address = "123 Main St"
    fake_loc1.zip_code = "12345"
    fake_loc1.city = "TestCity"
    fake_loc1.street = "Main St"
    fake_loc1.state = "TestState"
    fake_loc1.number = "101"
    fake_loc1.addition = "Apt 1"
    fake_loc1.type = "warehouse"

    fake_loc2 = MagicMock()
    fake_loc2.id = 2
    fake_loc2.address = "456 Elm St"
    fake_loc2.zip_code = "67890"
    fake_loc2.city = "OtherCity"
    fake_loc2.street = "Elm St"
    fake_loc2.state = "OtherState"
    fake_loc2.number = "202"
    fake_loc2.addition = None
    fake_loc2.type = "store"

    fake_session = MagicMock()
    # Simulate the query chain.
    fake_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [
        fake_loc1,
        fake_loc2,
    ]
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "resource": "/locations",
        "queryStringParameters": {"skip": "0", "limit": "10"},
    }

    response = get_locations(event)
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body = json.loads(response["body"])
    assert isinstance(body, list)
    assert len(body) == 2

    # Check first location's data.
    loc1 = body[0]
    assert loc1["id"] == 1
    assert loc1["address"] == "123 Main St"
    assert loc1["zip_code"] == "12345"
    assert loc1["city"] == "TestCity"
    assert loc1["street"] == "Main St"
    assert loc1["state"] == "TestState"
    assert loc1["number"] == "101"
    assert loc1["addition"] == "Apt 1"
    assert loc1["type"] == "warehouse"

    fake_session.close.assert_called_once()


def test_post_invalid_json():
    """
    Test that a POST /locations request with an invalid JSON body returns a 400 error.
    """
    event = {
        "httpMethod": "POST",
        "resource": "/locations",
        "body": "this is not json",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON in request body" in body["message"]


@patch("src.location_methods.get_session")
def test_post_invalid_location_type(mock_get_session):
    """
    Test that a POST /locations request with a location type that is not 'warehouse' or 'store'
    returns a 400 error.
    """
    payload = {
        "address": "789 Oak St",
        "zip_code": "54321",
        "city": "CityX",
        "street": "Oak St",
        "state": "StateX",
        "number": "303",
        "addition": "Suite 3",
        "type": "invalid-type",  # Invalid type
    }
    event = {
        "httpMethod": "POST",
        "resource": "/locations",
        "body": json.dumps(payload),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid location type" in body["message"]


@patch("src.location_methods.get_session")
def test_post_add_location_success(mock_get_session):
    """
    Test that a valid POST /locations request successfully adds a new location.
    We patch the Location constructor so that a fake location is returned.
    """
    # Create a fake location with expected attributes.
    fake_location = MagicMock()
    fake_location.id = 10
    fake_location.address = "789 Oak St"
    fake_location.zip_code = "54321"
    fake_location.city = "CityX"
    fake_location.street = "Oak St"
    fake_location.state = "StateX"
    fake_location.number = "303"
    fake_location.addition = "Suite 3"
    fake_location.type = "warehouse"

    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    # Patch the Location class used in add_location.

    with patch(
        "src.location_methods.Location", return_value=fake_location
    ) as _:
        payload = {
            "address": "789 Oak St",
            "zip_code": "54321",
            "city": "CityX",
            "street": "Oak St",
            "state": "StateX",
            "number": "303",
            "addition": "Suite 3",
            "type": "warehouse",
        }
        event = {
            "httpMethod": "POST",
            "resource": "/locations",
            "body": json.dumps(payload),
        }
        context = {}
        response = lambda_handler(event, context)
        # Expect a 201 Created response.
        assert response["statusCode"] == 201
        headers = response.get("headers", {})
        assert headers.get("Content-Type") == "application/json"
        body_resp = json.loads(response["body"])
        # Validate that the returned location details match the fake location.
        assert body_resp["id"] == fake_location.id
        assert body_resp["address"] == fake_location.address
        assert body_resp["zip_code"] == fake_location.zip_code
        assert body_resp["city"] == fake_location.city
        assert body_resp["street"] == fake_location.street
        assert body_resp["state"] == fake_location.state
        assert body_resp["number"] == fake_location.number
        assert body_resp["addition"] == fake_location.addition
        assert body_resp["type"] == fake_location.type

        fake_session.commit.assert_called_once()
        fake_session.refresh.assert_called_once_with(fake_location)
        fake_session.close.assert_called_once()
