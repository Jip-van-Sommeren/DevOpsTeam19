import json
from unittest.mock import MagicMock, patch

# Import the lambda_handler and get_purchases functions from your module.
from src.purchases_methods import lambda_handler, get_purchases


def test_lambda_handler_not_found():
    """
    Test that an event with an unsupported resource/method returns a 404.
    """
    event = {
        "httpMethod": "POST",  # Not a GET request for /purchases
        "resource": "/invalid",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Not Found" in body["message"]


@patch("src.purchases_methods.get_session")
def test_get_purchases_without_user_id(mock_get_session):
    """
    Test GET /purchases without a user_id filter.
    This simulates two purchase records with associated purchased_items.
    """
    # Create two fake purchase objects.
    fake_purchase1 = MagicMock()
    fake_purchase1.id = 1
    fake_purchase1.user_id = 10
    fake_item1 = MagicMock()
    fake_item1.item_id = 101
    fake_item1.quantity = 2
    fake_purchase1.purchased_items = [fake_item1]

    fake_purchase2 = MagicMock()
    fake_purchase2.id = 2
    fake_purchase2.user_id = 20
    fake_item2 = MagicMock()
    fake_item2.item_id = 102
    fake_item2.quantity = 5
    fake_purchase2.purchased_items = [fake_item2]

    # Create a fake session and simulate the query chain.
    fake_session = MagicMock()
    # session.query(Purchase)
    fake_query = fake_session.query.return_value
    # .options(joinedload(...))
    fake_options = fake_query.options.return_value
    # .offset(skip)
    fake_offset = fake_options.offset.return_value
    # .limit(limit)
    fake_limit = fake_offset.limit.return_value
    # .all() returns our list of fake purchases.
    fake_limit.all.return_value = [fake_purchase1, fake_purchase2]
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "resource": "/purchases",
        "queryStringParameters": {"skip": "0", "limit": "10"},
    }
    response = get_purchases(event)
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    purchases_list = json.loads(response["body"])
    assert isinstance(purchases_list, list)
    assert len(purchases_list) == 2

    # Verify details of the first purchase.
    p1 = purchases_list[0]
    assert p1["id"] == 1
    assert p1["user_id"] == 10
    assert isinstance(p1["items"], list)
    assert len(p1["items"]) == 1
    assert p1["items"][0]["item_id"] == 101
    assert p1["items"][0]["quantity"] == 2

    # Verify details of the second purchase.
    p2 = purchases_list[1]
    assert p2["id"] == 2
    assert p2["user_id"] == 20
    assert isinstance(p2["items"], list)
    assert len(p2["items"]) == 1
    assert p2["items"][0]["item_id"] == 102
    assert p2["items"][0]["quantity"] == 5

    # Ensure the session is closed.
    fake_session.close.assert_called_once()


@patch("src.purchases_methods.get_session")
def test_get_purchases_with_user_id(mock_get_session):
    """
    Test GET /purchases when a user_id query parameter is provided.
    Only purchases matching the user_id should be returned.
    """
    fake_purchase = MagicMock()
    fake_purchase.id = 3
    fake_purchase.user_id = 30
    fake_item = MagicMock()
    fake_item.item_id = 103
    fake_item.quantity = 7
    fake_purchase.purchased_items = [fake_item]

    fake_session = MagicMock()
    # Set up the query chain for the filter case.
    fake_query = fake_session.query.return_value
    fake_options = fake_query.options.return_value
    fake_filter = fake_options.filter.return_value
    fake_offset = fake_filter.offset.return_value
    fake_limit = fake_offset.limit.return_value
    fake_limit.all.return_value = [fake_purchase]
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "resource": "/purchases",
        "queryStringParameters": {"skip": "0", "limit": "10", "user_id": "30"},
    }
    response = get_purchases(event)
    assert response["statusCode"] == 200
    purchases_list = json.loads(response["body"])
    assert len(purchases_list) == 1
    p = purchases_list[0]
    assert p["id"] == 3
    assert p["user_id"] == 30
    assert isinstance(p["items"], list)
    assert len(p["items"]) == 1
    assert p["items"][0]["item_id"] == 103
    assert p["items"][0]["quantity"] == 7

    fake_session.close.assert_called_once()
