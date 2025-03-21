import json
import pytest
from unittest.mock import MagicMock, patch

# Import the lambda_handler and get_reservations from your module.
from src.reservations_methods import lambda_handler, get_reservations


def test_lambda_handler_not_found():
    """
    Test that a request not matching the /reservations GET endpoint returns 404.
    """
    event = {"httpMethod": "POST", "resource": "/unknown"}  # Wrong HTTP method
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Not Found" in body["message"]


@patch("src.reservations_methods.get_session")
def test_get_reservations_without_user_id(mock_get_session):
    """
    Test GET /reservations when no user_id is provided.
    This simulates two fake reservations with associated reserved items.
    """
    # Create two fake Reservation objects.
    fake_res1 = MagicMock()
    fake_res1.id = 1
    fake_res1.user_id = 10
    fake_item1 = MagicMock()
    fake_item1.item_id = 100
    fake_item1.quantity = 3
    fake_res1.reserved_items = [fake_item1]

    fake_res2 = MagicMock()
    fake_res2.id = 2
    fake_res2.user_id = 20
    fake_item2 = MagicMock()
    fake_item2.item_id = 101
    fake_item2.quantity = 5
    fake_res2.reserved_items = [fake_item2]

    # Create a fake session and simulate the query chain.
    fake_session = MagicMock()
    # session.query(Reservation)
    fake_query = fake_session.query.return_value
    # .options(joinedload(Reservation.reserved_items))
    fake_options = fake_query.options.return_value
    # .offset(skip)
    fake_offset = fake_options.offset.return_value
    # .limit(limit)
    fake_limit = fake_offset.limit.return_value
    # .all() returns our list of fake reservations.
    fake_limit.all.return_value = [fake_res1, fake_res2]
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "resource": "/reservations",
        "queryStringParameters": {"skip": "0", "limit": "10"},
    }
    context = {}
    response = get_reservations(event)
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    reservations_list = json.loads(response["body"])
    assert isinstance(reservations_list, list)
    assert len(reservations_list) == 2

    # Verify first reservation's details.
    res1 = reservations_list[0]
    assert res1["id"] == 1
    assert res1["user_id"] == 10
    assert isinstance(res1["items"], list)
    assert len(res1["items"]) == 1
    assert res1["items"][0]["item_id"] == 100
    assert res1["items"][0]["quantity"] == 3

    # Verify second reservation's details.
    res2 = reservations_list[1]
    assert res2["id"] == 2
    assert res2["user_id"] == 20
    assert isinstance(res2["items"], list)
    assert len(res2["items"]) == 1
    assert res2["items"][0]["item_id"] == 101
    assert res2["items"][0]["quantity"] == 5

    # Ensure the session is closed.
    fake_session.close.assert_called_once()


@patch("src.reservations_methods.get_session")
def test_get_reservations_with_user_id(mock_get_session):
    """
    Test GET /reservations when a user_id query parameter is provided.
    Only reservations matching the provided user_id should be returned.
    """
    fake_res = MagicMock()
    fake_res.id = 3
    fake_res.user_id = 30
    fake_item = MagicMock()
    fake_item.item_id = 102
    fake_item.quantity = 7
    fake_res.reserved_items = [fake_item]

    fake_session = MagicMock()
    # Setup query chain for filtering by user_id.
    fake_query = fake_session.query.return_value
    fake_options = fake_query.options.return_value
    fake_filter = fake_options.filter.return_value
    fake_offset = fake_filter.offset.return_value
    fake_limit = fake_offset.limit.return_value
    fake_limit.all.return_value = [fake_res]
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "resource": "/reservations",
        "queryStringParameters": {"skip": "0", "limit": "10", "user_id": "30"},
    }
    context = {}
    response = get_reservations(event)
    assert response["statusCode"] == 200
    reservations_list = json.loads(response["body"])
    assert isinstance(reservations_list, list)
    assert len(reservations_list) == 1

    res = reservations_list[0]
    assert res["id"] == 3
    assert res["user_id"] == 30
    assert isinstance(res["items"], list)
    assert len(res["items"]) == 1
    assert res["items"][0]["item_id"] == 102
    assert res["items"][0]["quantity"] == 7

    fake_session.close.assert_called_once()
