from unittest.mock import MagicMock, patch

from src.purchase_post import lambda_handler


# ---------------------------------------------------------------------
# Test helper: simulate a Purchase instance.
# ---------------------------------------------------------------------
def fake_purchase_instance(purchase_id, user_id, payment_token):
    fake = MagicMock()
    fake.id = purchase_id
    fake.user_id = user_id
    fake.payment_token = payment_token
    return fake


# ---------------------------------------------------------------------
# Test 1: With reservation_id provided and no items.
# ---------------------------------------------------------------------
@patch("src.purchase_post.get_session")
@patch("src.purchase_post.PurchasedItem")
@patch("src.purchase_post.Purchase")
def test_lambda_handler_with_reservation(
    mock_Purchase, mock_PurchasedItem, mock_get_session
):
    # Arrange: create a fake session.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    # Simulate a new purchase (no items provided).
    fake_purchase = fake_purchase_instance(100, 1, "abc")
    mock_Purchase.return_value = fake_purchase

    # Build purchase data with a reservation_id.
    purchase_data = {
        "user_id": 1,
        "payment_token": "abc",
        "status": "pending",
        "reservation_id": 50,
        # Note: no "items" key is provided.
    }
    event = {"data": purchase_data}
    context = {}

    # Act
    response = lambda_handler(event, context)

    # Assert: Expect a 201 response with reservation_id and purchase_id.
    assert response["statusCode"] == 201
    assert response["reservation_id"] == 50
    assert response["purchase_id"] == 100

    # The response_body should include the purchase details and an empty
    # items list.
    resp_body = response["response_body"]
    assert resp_body["purchase"]["id"] == 100
    assert resp_body["purchase"]["user_id"] == 1
    assert resp_body["purchase"]["payment_token"] == "abc"
    assert resp_body["items"] == []

    # Verify that the session's commit, refresh, and close were called.
    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once_with(fake_purchase)
    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------
# Test 2: Without reservation_id and with items provided.
# ---------------------------------------------------------------------
@patch("src.purchase_post.get_session")
@patch("src.purchase_post.PurchasedItem")
@patch("src.purchase_post.Purchase")
def test_lambda_handler_without_reservation_with_items(
    mock_Purchase, mock_PurchasedItem, mock_get_session
):
    # Arrange: create a fake session.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    # Simulate a new purchase.
    fake_purchase = fake_purchase_instance(101, 2, "def")
    mock_Purchase.return_value = fake_purchase

    # Prepare side_effect for PurchasedItem so that each call
    # returns a fake object
    # with attributes matching the input.
    def purchased_item_side_effect(
        purchase_id, item_id, location_id, quantity
    ):
        fake_pi = MagicMock()
        fake_pi.item_id = item_id
        fake_pi.location_id = location_id
        fake_pi.quantity = quantity
        return fake_pi

    mock_PurchasedItem.side_effect = purchased_item_side_effect

    # Build purchase data with items (and no reservation_id).
    purchase_data = {
        "user_id": 2,
        "payment_token": "def",
        "status": "completed",
        "items": [
            {"item_id": 10, "location_id": 5, "quantity": 3},
            {"item_id": 11, "location_id": 6, "quantity": 2},
        ],
    }
    event = {"data": purchase_data}
    context = {}

    # Act
    response = lambda_handler(event, context)

    # Assert: Expect a 201 response with purchase_id and a
    # "stock_operation" key.
    assert response["statusCode"] == 201
    assert response["purchase_id"] == 101
    assert response["stock_operation"] == "deduct"

    # Check that the response_body contains the purchase details
    # and inserted items.
    resp_body = response["response_body"]
    assert resp_body["purchase"]["id"] == 101
    assert resp_body["purchase"]["user_id"] == 2
    assert resp_body["purchase"]["payment_token"] == "def"
    inserted_items = resp_body["items"]
    assert len(inserted_items) == 2

    # Verify the first inserted item.
    assert inserted_items[0]["item_id"] == 10
    assert inserted_items[0]["location_id"] == 5
    assert inserted_items[0]["quantity"] == 3
    # Verify the second inserted item.
    assert inserted_items[1]["item_id"] == 11
    assert inserted_items[1]["location_id"] == 6
    assert inserted_items[1]["quantity"] == 2

    assert fake_session.commit.call_count == 2
    fake_session.refresh.assert_called_once_with(fake_purchase)
    fake_session.close.assert_called_once()
