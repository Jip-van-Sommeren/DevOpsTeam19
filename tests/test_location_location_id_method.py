import json
from unittest.mock import MagicMock, patch
from src.location_location_id_method import lambda_handler


def create_fake_location():
    fake_location = MagicMock()
    fake_location.id = 1
    fake_location.address = "123 Main St"
    fake_location.zip_code = "12345"
    fake_location.city = "CityName"
    fake_location.street = "Main St"
    fake_location.state = "StateName"
    fake_location.number = "123"
    fake_location.addition = "Apt 4"
    fake_location.type = "residential"
    return fake_location


# ------------------------------------------------------------------------------
# Test: Missing location_id in pathParameters returns 400.
# ------------------------------------------------------------------------------
def test_lambda_handler_missing_location_id():
    event = {"httpMethod": "GET", "pathParameters": {}}  # location_id missing
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing location_id in path" in body["message"]


# ------------------------------------------------------------------------------
# Tests for GET method (get_location)
# ------------------------------------------------------------------------------
@patch("src.location_location_id_method.get_session")
def test_get_location_found(mock_get_session):
    fake_location = create_fake_location()
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_location
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "GET", "pathParameters": {"location_id": "1"}}
    context = {}
    response = lambda_handler(event, context)

    # Verify successful response.
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body = json.loads(response["body"])
    # Verify all expected fields.
    assert body["id"] == fake_location.id
    assert body["address"] == fake_location.address
    assert body["zip_code"] == fake_location.zip_code
    assert body["city"] == fake_location.city
    assert body["street"] == fake_location.street
    assert body["state"] == fake_location.state
    assert body["number"] == fake_location.number
    assert body["addition"] == fake_location.addition
    assert body["type"] == fake_location.type
    fake_session.close.assert_called_once()


@patch("src.location_location_id_method.get_session")
def test_get_location_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "GET", "pathParameters": {"location_id": "999"}}
    context = {}
    response = lambda_handler(event, context)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "location not found" in body["message"]
    fake_session.close.assert_called_once()


# ------------------------------------------------------------------------------
# Tests for DELETE method (delete_location)
# ------------------------------------------------------------------------------
@patch("src.location_location_id_method.get_session")
def test_delete_location_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "DELETE", "pathParameters": {"location_id": "999"}}
    context = {}
    response = lambda_handler(event, context)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "location not found" in body["message"]
    fake_session.close.assert_called_once()


@patch("src.location_location_id_method.get_session")
def test_delete_location_success(mock_get_session):
    fake_location = create_fake_location()
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_location
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "DELETE", "pathParameters": {"location_id": "1"}}
    context = {}
    response = lambda_handler(event, context)

    # Expect a successful deletion response with the location id.
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body = json.loads(response["body"])
    assert body["id"] == fake_location.id
    fake_session.delete.assert_called_once_with(fake_location)
    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()


# ------------------------------------------------------------------------------
# Tests for PUT method (update_location)
# ------------------------------------------------------------------------------
@patch("src.location_location_id_method.get_session")
def test_update_location_invalid_json(mock_get_session):
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"location_id": "1"},
        "body": "invalid json",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["message"]


@patch("src.location_location_id_method.get_session")
def test_update_location_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    payload = {
        "address": "456 New St",
        "zip_code": "67890",
        "city": "New City",
        "street": "New St",
        "state": "NewState",
        "number": "456",
        "addition": "Suite 2",
        "type": "commercial",
    }
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"location_id": "1"},
        "body": json.dumps(payload),
    }
    context = {}
    response = lambda_handler(event, context)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "location not found" in body["message"]
    fake_session.close.assert_called_once()


@patch("src.location_location_id_method.get_session")
def test_update_location_success(mock_get_session):
    fake_location = create_fake_location()
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_location
    )
    mock_get_session.return_value = fake_session

    payload = {
        "address": "456 New St",
        "zip_code": "67890",
        "city": "New City",
        "street": "New St",
        "state": "NewState",
        "number": "456",
        "addition": "Suite 2",
        "type": "commercial",
    }
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"location_id": "1"},
        "body": json.dumps(payload),
    }
    context = {}
    response = lambda_handler(event, context)

    # Expect a successful update returning 200 and the updated fields.
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body = json.loads(response["body"])
    assert body["id"] == fake_location.id
    assert body["name"] == payload["address"]
    assert body["description"] == payload["zip_code"]
    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once_with(fake_location)
    fake_session.close.assert_called_once()


# ------------------------------------------------------------------------------
# Test for unsupported HTTP method (e.g., PATCH)
# ------------------------------------------------------------------------------
def test_method_not_allowed():
    event = {"httpMethod": "PATCH", "pathParameters": {"location_id": "1"}}
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert "Method PATCH not allowed" in body["message"]
