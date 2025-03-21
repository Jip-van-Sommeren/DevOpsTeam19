import json
import datetime
import pytest
from unittest.mock import MagicMock, patch

# Import the lambda_handler (and helper functions if needed) from your module.
from src.purchases_purchase_id_method import (
    lambda_handler,
    get_purchase,
    delete_purchase,
    update_purchase,
)


# -------------------------------------------------------------------------
# Helper: Create fake purchase and purchased item objects.
# -------------------------------------------------------------------------
def create_fake_purchase(
    purchase_id=1, user_id=10, payment_token="abc", status="completed"
):
    fake_purchase = MagicMock()
    fake_purchase.id = purchase_id
    fake_purchase.user_id = user_id
    fake_purchase.payment_token = payment_token
    fake_purchase.status = status
    # Create fake datetime objects.
    fake_created_at = datetime.datetime(2023, 1, 1, 12, 0, 0)
    fake_updated_at = datetime.datetime(2023, 1, 2, 12, 0, 0)
    fake_purchase.created_at = fake_created_at
    fake_purchase.updated_at = fake_updated_at
    # Simulate purchased_items list.
    fake_item = MagicMock()
    fake_item.item_id = 100
    fake_item.quantity = 3
    fake_purchase.purchased_items = [fake_item]
    return fake_purchase


# -------------------------------------------------------------------------
# Test: Missing purchase_id in path parameters should return 400.
# -------------------------------------------------------------------------
def test_lambda_handler_missing_purchase_id():
    event = {"httpMethod": "GET", "pathParameters": {}}  # purchase_id missing
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing purchase_id in path" in body["message"]


# -------------------------------------------------------------------------
# GET purchase: when purchase is found.
# -------------------------------------------------------------------------
@patch("src.purchases_purchase_id_method.get_session")
def test_get_purchase_found(mock_get_session):
    fake_purchase = create_fake_purchase(purchase_id=1)
    fake_session = MagicMock()
    # Simulate the query chain returning the fake purchase.
    fake_session.query.return_value.options.return_value.filter.return_value.first.return_value = (
        fake_purchase
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "GET", "pathParameters": {"purchase_id": "1"}}
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body = json.loads(response["body"])
    assert body["id"] == fake_purchase.id
    assert body["user_id"] == fake_purchase.user_id
    assert body["payment_token"] == fake_purchase.payment_token
    # Purchased items list is built from the fake purchase.
    assert isinstance(body["purchase_items"], list)
    assert len(body["purchase_items"]) == 1
    assert (
        body["purchase_items"][0]["item_id"]
        == fake_purchase.purchased_items[0].item_id
    )
    assert (
        body["purchase_items"][0]["quantity"]
        == fake_purchase.purchased_items[0].quantity
    )
    # Timestamps are ISO formatted.
    assert body["created_at"] == fake_purchase.created_at.isoformat()
    assert body["updated_at"] == fake_purchase.updated_at.isoformat()

    fake_session.close.assert_called_once()


# -------------------------------------------------------------------------
# GET purchase: when purchase is not found.
# -------------------------------------------------------------------------
@patch("src.purchases_purchase_id_method.get_session")
def test_get_purchase_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_session.query.return_value.options.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "GET", "pathParameters": {"purchase_id": "999"}}
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Purchase not found" in body["message"]
    fake_session.close.assert_called_once()


# -------------------------------------------------------------------------
# DELETE purchase: when purchase is found.
# -------------------------------------------------------------------------
@patch("src.purchases_purchase_id_method.get_session")
def test_delete_purchase_found(mock_get_session):
    fake_purchase = create_fake_purchase(
        purchase_id=2, user_id=20, payment_token="def"
    )
    fake_session = MagicMock()
    # Simulate query returning the purchase.
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_purchase
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "DELETE", "pathParameters": {"purchase_id": "2"}}
    context = {}
    response = lambda_handler(event, context)
    # Expected response contains purchase id, user_id as name, and payment_token as description.
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body = json.loads(response["body"])
    assert body["id"] == fake_purchase.id
    assert body["name"] == fake_purchase.user_id
    assert body["description"] == fake_purchase.payment_token

    # Verify deletion of associated purchased items is triggered.
    fake_session.query.return_value.filter.assert_called()  # Called for PurchasedItem deletion.
    fake_session.delete.assert_called_once_with(fake_purchase)
    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()


# -------------------------------------------------------------------------
# DELETE purchase: when purchase is not found.
# -------------------------------------------------------------------------
@patch("src.purchases_purchase_id_method.get_session")
def test_delete_purchase_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "DELETE", "pathParameters": {"purchase_id": "999"}}
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Purchase not found" in body["message"]
    fake_session.close.assert_called_once()


# -------------------------------------------------------------------------
# PUT purchase: invalid JSON body should return 400.
# -------------------------------------------------------------------------
def test_update_purchase_invalid_json():
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"purchase_id": "1"},
        "body": "invalid json",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["message"]


# -------------------------------------------------------------------------
# PUT purchase: when purchase is not found.
# -------------------------------------------------------------------------
@patch("src.purchases_purchase_id_method.get_session")
def test_update_purchase_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    payload = {"user_id": 30, "status": "shipped"}
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"purchase_id": "1"},
        "body": json.dumps(payload),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Purchase not found" in body["message"]
    fake_session.close.assert_called_once()


# -------------------------------------------------------------------------
# PUT purchase: successful update.
# -------------------------------------------------------------------------
@patch("src.purchases_purchase_id_method.get_session")
def test_update_purchase_success(mock_get_session):
    fake_purchase = create_fake_purchase(
        purchase_id=3, user_id=15, payment_token="ghi", status="pending"
    )
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_purchase
    )
    mock_get_session.return_value = fake_session

    # Prepare payload to update user_id and status.
    payload = {"user_id": 25, "status": "shipped"}
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"purchase_id": "3"},
        "body": json.dumps(payload),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body_resp = json.loads(response["body"])
    # Note: The update_purchase function maps purchase.user_id to "name" and payment_token to "description".
    assert body_resp["id"] == fake_purchase.id
    assert body_resp["name"] == payload["user_id"]  # Updated user_id
    assert (
        body_resp["description"] == fake_purchase.payment_token
    )  # Remains unchanged
    assert body_resp["status"] == payload["status"]

    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once_with(fake_purchase)
    fake_session.close.assert_called_once()


# -------------------------------------------------------------------------
# Test for unsupported HTTP method.
# -------------------------------------------------------------------------
def test_lambda_handler_method_not_allowed():
    event = {"httpMethod": "PATCH", "pathParameters": {"purchase_id": "1"}}
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert "Method PATCH not allowed" in body["message"]
