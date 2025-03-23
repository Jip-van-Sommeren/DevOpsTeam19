import pytest
from unittest.mock import MagicMock, patch
from src.reservation_post import lambda_handler


@patch("src.reservation_post.get_session")
@patch("src.reservation_post.ReservedItem")
@patch("src.reservation_post.Reservation")
def test_lambda_handler_success(
    mock_Reservation, mock_ReservedItem, mock_get_session
):
    # Arrange: Create a fake session.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    # Fake Reservation instance.
    fake_reservation = MagicMock()
    fake_reservation.id = 123
    fake_reservation.user_id = 42
    fake_reservation.status = "reserved"
    mock_Reservation.return_value = fake_reservation

    def reserved_item_side_effect(
        reservation_id, item_id, location_id, quantity
    ):
        fake_item = MagicMock()
        fake_item.reservation_id = reservation_id
        fake_item.item_id = item_id
        fake_item.location_id = location_id
        fake_item.quantity = quantity
        return fake_item

    mock_ReservedItem.side_effect = reserved_item_side_effect

    # Build a valid event payload.
    purchase_data = {
        "user_id": 42,
        "items": [
            {"item_id": 10, "location_id": 5, "quantity": 2},
            {"item_id": 11, "location_id": 6, "quantity": 3},
        ],
    }
    event = {"data": purchase_data}
    context = {}

    # Act: Call the lambda_handler.
    response = lambda_handler(event, context)

    # Assert: Verify the response structure.
    assert response["statusCode"] == 201
    assert response["reservation_id"] == 123

    response_body = response["response_body"]
    assert response_body["reservation"]["id"] == 123
    assert response_body["reservation"]["user_id"] == 42
    assert response_body["reservation"]["status"] == "reserved"

    # Verify that two reserved items are returned.
    inserted_items = response_body["items"]
    assert len(inserted_items) == 2

    # Check the first reserved item.
    first_item = inserted_items[0]
    assert first_item["item_id"] == 10
    assert first_item["location_id"] == 5
    assert first_item["quantity"] == 2

    # Check the second reserved item.
    second_item = inserted_items[1]
    assert second_item["item_id"] == 11
    assert second_item["location_id"] == 6
    assert second_item["quantity"] == 3

    assert fake_session.commit.call_count == 2
    fake_session.refresh.assert_called_once_with(fake_reservation)
    fake_session.close.assert_called_once()


def test_lambda_handler_missing_user_id():
    event = {"data": {"items": [{"item_id": 10, "quantity": 2}]}}
    context = {}
    with pytest.raises(ValueError) as excinfo:
        lambda_handler(event, context)
    assert "Missing user_id in input" in str(excinfo.value)


def test_lambda_handler_no_items():
    event = {"data": {"user_id": 42}}
    context = {}
    with pytest.raises(ValueError) as excinfo:
        lambda_handler(event, context)
    assert "No items provided to update" in str(excinfo.value)
