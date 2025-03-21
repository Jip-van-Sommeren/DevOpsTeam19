import json
import pytest
from unittest.mock import MagicMock, patch

# Import the lambda_handler and helper functions from your module.
from src.stock_methods import lambda_handler, get_items, add_items

# ---------------------- Helper Tests for GET ---------------------------


@patch("src.stock_methods.get_session")
def test_get_items_success(mock_get_session):
    # Create a fake ItemStock object.
    fake_item = MagicMock()
    fake_item.id = 1
    fake_item.item_id = "item1"
    fake_item.location_id = "loc1"
    fake_item.quantity = 100

    # Create a fake session and simulate the query chain.
    fake_session = MagicMock()
    fake_query = MagicMock()
    # IMPORTANT: Ensure that filter returns a query object so the chain continues.
    fake_query.filter.return_value = fake_query
    fake_offset = MagicMock()
    fake_limit = MagicMock()
    fake_limit.all.return_value = [fake_item]
    fake_offset.limit.return_value = fake_limit
    fake_query.offset.return_value = fake_offset
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "resource": "/stock",
        "queryStringParameters": {
            "skip": "0",
            "limit": "10",
            "location_id": "loc1",
        },
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body_resp = json.loads(response["body"])
    print(body_resp)  # For debugging if needed
    assert isinstance(body_resp, list)
    assert len(body_resp) == 1
    fake_session.close.assert_called_once()


@patch("src.stock_methods.get_session")
def test_get_items_empty(mock_get_session):
    # Simulate no items found.
    fake_session = MagicMock()
    fake_query = MagicMock()
    fake_offset = MagicMock()
    fake_limit = MagicMock()
    fake_limit.all.return_value = []
    fake_offset.limit.return_value = fake_limit
    fake_query.offset.return_value = fake_offset
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "resource": "/stock",
        "queryStringParameters": {"skip": "0", "limit": "10"},
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200
    body_resp = json.loads(response["body"])
    assert isinstance(body_resp, list)
    assert len(body_resp) == 0
    fake_session.close.assert_called_once()


# ---------------------- Helper Tests for POST ---------------------------


@patch("src.stock_methods.get_session")
@patch("src.stock_methods.ItemStock")
def test_add_items_success(mock_ItemStock, mock_get_session):
    # Setup a fake session.
    fake_session = MagicMock()

    # Set up session.refresh: simulate that it sets an id on the object if not set.
    def refresh_side_effect(item):
        if not hasattr(item, "id") or item.id is None:
            item.id = 1  # For simplicity, assign 1.

    fake_session.refresh.side_effect = refresh_side_effect
    mock_get_session.return_value = fake_session

    # Create two fake items via the patched ItemStock constructor.
    fake_item1 = MagicMock()
    fake_item1.item_id = "item1"
    fake_item1.location_id = "loc1"
    fake_item1.quantity = 50
    fake_item1.id = 101  # Simulate that refresh sets id.
    fake_item2 = MagicMock()
    fake_item2.item_id = "item2"
    fake_item2.location_id = "loc2"
    fake_item2.quantity = 75
    fake_item2.id = 102

    # When ItemStock is called, return these fake items in order.
    mock_ItemStock.side_effect = [fake_item1, fake_item2]

    # Prepare payload with a list of items.
    payload = {
        "items": [
            {"item_id": "item1", "location_id": "loc1", "quantity": 50},
            {"item_id": "item2", "location_id": "loc2", "quantity": 75},
        ]
    }
    event = {
        "httpMethod": "POST",
        "resource": "/stock",
        "body": json.dumps(payload),
    }
    context = {}
    response = lambda_handler(event, context)
    # Expect a 201 response from add_items.
    assert response["statusCode"] == 201
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body_resp = json.loads(response["body"])
    # Should be a list of two inserted items.
    assert isinstance(body_resp, list)
    assert len(body_resp) == 2

    # Verify details of first inserted item.
    inserted_item1 = body_resp[0]
    assert inserted_item1["id"] == fake_item1.id
    assert inserted_item1["item_id"] == fake_item1.item_id
    assert inserted_item1["location_id"] == fake_item1.location_id
    assert inserted_item1["quantity"] == fake_item1.quantity

    # Verify details of second inserted item.
    inserted_item2 = body_resp[1]
    assert inserted_item2["id"] == fake_item2.id
    assert inserted_item2["item_id"] == fake_item2.item_id
    assert inserted_item2["location_id"] == fake_item2.location_id
    assert inserted_item2["quantity"] == fake_item2.quantity

    # Verify that add_all, commit, refresh, and close were called appropriately.
    fake_session.add_all.assert_called_once()  # Items added in bulk.
    # commit should be called once.
    fake_session.commit.assert_called_once()
    # refresh should be called for each fake item.
    assert fake_session.refresh.call_count == 2
    fake_session.close.assert_called_once()


# ---------------------- Test for Invalid JSON and 404 ---------------------------


def test_lambda_handler_invalid_json():
    event = {
        "httpMethod": "POST",
        "resource": "/stock",
        "body": "invalid json",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body_resp = json.loads(response["body"])
    assert "Invalid JSON in request body" in body_resp["message"]


def test_lambda_handler_unknown_resource():
    event = {
        "httpMethod": "GET",
        "resource": "/unknown",
        "body": json.dumps({}),
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body_resp = json.loads(response["body"])
    assert "Not Found" in body_resp["message"]
