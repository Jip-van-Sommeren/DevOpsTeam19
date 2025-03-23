import json
from unittest.mock import MagicMock, patch
from src.stock_item_id_methods import lambda_handler


# ---------------------------------------------------------------------------
# Test: Missing item_id in path parameters returns 400.
# ---------------------------------------------------------------------------
def test_lambda_handler_missing_item_id():
    event = {"httpMethod": "GET", "pathParameters": {}}  # missing item_id
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing item_id in path" in body["message"]


# ---------------------------------------------------------------------------
# Test: Invalid JSON in request body returns 400.
# ---------------------------------------------------------------------------
def test_lambda_handler_invalid_json():
    event = {
        "httpMethod": "GET",
        "pathParameters": {"item_id": "1"},
        "body": "not a valid json",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["message"]


# ---------------------------------------------------------------------------
# GET method tests
# ---------------------------------------------------------------------------
@patch("src.stock_item_id_methods.get_session")
def test_get_item_found(mock_get_session):
    # Create a fake item object.
    fake_item = MagicMock()
    fake_item.id = 1
    fake_item.item_id = "1"
    fake_item.location_id = "loc1"
    fake_item.quantity = 50

    fake_session = MagicMock()
    # Simulate query chain: query(...).filter(...).first() returns fake_item.
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.first.return_value = fake_item
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps({"location_id": "loc1"}),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body_resp = json.loads(response["body"])
    assert body_resp["id"] == fake_item.id
    assert body_resp["item_id"] == fake_item.item_id
    assert body_resp["location_id"] == fake_item.location_id
    assert body_resp["quantity"] == fake_item.quantity
    fake_session.close.assert_called_once()


@patch("src.stock_item_id_methods.get_session")
def test_get_item_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.first.return_value = None
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps({"location_id": "loc1"}),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body_resp = json.loads(response["body"])
    assert "Item not found" in body_resp["message"]
    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# DELETE method tests
# ---------------------------------------------------------------------------
@patch("src.stock_item_id_methods.get_session")
def test_delete_item_found(mock_get_session):
    fake_item = MagicMock()
    fake_item.id = 2
    fake_item.item_id = "1"
    fake_item.location_id = "loc1"
    fake_item.quantity = 30

    fake_session = MagicMock()
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.first.return_value = fake_item
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "DELETE",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps({"location_id": "loc1"}),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body_resp = json.loads(response["body"])
    assert body_resp["id"] == fake_item.id
    assert body_resp["item_id"] == fake_item.item_id
    assert body_resp["location_id"] == fake_item.location_id
    assert body_resp["quantity"] == fake_item.quantity
    fake_session.delete.assert_called_once_with(fake_item)
    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()


@patch("src.stock_item_id_methods.get_session")
def test_delete_item_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.first.return_value = None
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "DELETE",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps({"location_id": "loc1"}),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body_resp = json.loads(response["body"])
    assert "Item not found" in body_resp["message"]
    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# PUT method tests (update_stock)
# ---------------------------------------------------------------------------
@patch("src.stock_item_id_methods.get_session")
def test_put_update_stock_reset(mock_get_session):
    fake_item = MagicMock()
    fake_item.id = 3
    fake_item.item_id = "1"
    fake_item.location_id = "loc1"
    fake_item.quantity = 100

    fake_session = MagicMock()
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.first.return_value = fake_item
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    payload = {"item_id": "1", "location_id": "loc1", "quantity": 80}
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps(payload),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200
    body_resp = json.loads(response["body"])
    assert "Stock update successful" in body_resp["message"]
    updated = body_resp["updated"]
    # For reset, the quantity is overwritten.
    assert updated["quantity"] == 80

    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once_with(fake_item)
    fake_session.close.assert_called_once()


@patch("src.stock_item_id_methods.get_session")
def test_put_update_stock_deduct(mock_get_session):
    fake_item = MagicMock()
    fake_item.id = 4
    fake_item.item_id = "1"
    fake_item.location_id = "loc1"
    fake_item.quantity = 100

    fake_session = MagicMock()
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.first.return_value = fake_item
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    payload = {
        "item_id": "1",
        "location_id": "loc1",
        "quantity": 30,
        "stock_operation": "deduct",
    }
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps(payload),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200
    body_resp = json.loads(response["body"])
    updated = body_resp["updated"]
    # For deduct, 100 - 30 = 70.
    assert updated["quantity"] == 70

    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once_with(fake_item)
    fake_session.close.assert_called_once()


@patch("src.stock_item_id_methods.get_session")
def test_put_update_stock_add(mock_get_session):
    fake_item = MagicMock()
    fake_item.id = 5
    fake_item.item_id = "1"
    fake_item.location_id = "loc1"
    fake_item.quantity = 50

    fake_session = MagicMock()
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.first.return_value = fake_item
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    payload = {
        "item_id": "1",
        "location_id": "loc1",
        "quantity": 20,
        "stock_operation": "add",
    }
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps(payload),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200
    body_resp = json.loads(response["body"])
    updated = body_resp["updated"]
    # For add, 50 + 20 = 70.
    assert updated["quantity"] == 70

    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once_with(fake_item)
    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# Test: Unsupported HTTP method.
# ---------------------------------------------------------------------------
def test_lambda_handler_method_not_allowed():
    event = {
        "httpMethod": "PATCH",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps({}),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 405
    body_resp = json.loads(response["body"])
    assert "Method PATCH not allowed" in body_resp["message"]
