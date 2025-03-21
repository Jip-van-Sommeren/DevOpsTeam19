import json
import pytest
from unittest.mock import MagicMock, patch

# Import the lambda_handler from your module.
from src.update_stock import lambda_handler


@patch("src.update_stock.send_stock_alert")
@patch("src.update_stock.update_stock_for_item")
@patch("src.update_stock.get_session")
def test_lambda_handler_success_deduct(
    mock_get_session, mock_update_stock, mock_send_alert
):
    # Setup a fake session.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    # Simulate update_stock_for_item for two items:
    # First item: updated to quantity 5 (<10, should trigger alert)
    # Second item: updated to quantity 15 (no alert)
    updated_item1 = {"id": 1, "quantity": 5}
    updated_item2 = {"id": 2, "quantity": 15}
    mock_update_stock.side_effect = [updated_item1, updated_item2]

    # Build an event with valid data.
    event = {
        "data": {
            "response_body": {
                "items": [
                    {
                        "item_id": "item1",
                        "location_id": "loc1",
                        "quantity": 10,
                    },
                    {"item_id": "item2", "location_id": "loc2", "quantity": 5},
                ]
            },
            "operation": "deduct",
            "reservation_id": "res123",
            "purchase_id": "pur456",
        }
    }
    context = {}

    response = lambda_handler(event, context)

    # Verify response format.
    assert response["statusCode"] == 201
    assert response["reservation_id"] == "res123"
    assert response["purchase_id"] == "pur456"
    assert response["response_body"] == event["data"]["response_body"]
    assert response["updated_items"] == [updated_item1, updated_item2]

    # update_stock_for_item should be called once per item.
    assert mock_update_stock.call_count == 2

    # For "deduct", an alert is sent for items with quantity < 10.
    mock_send_alert.assert_called_once_with(
        updated_item1["id"], updated_item1["quantity"]
    )

    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()


@patch("src.update_stock.send_stock_alert")
@patch("src.update_stock.update_stock_for_item")
@patch("src.update_stock.get_session")
def test_lambda_handler_success_non_deduct(
    mock_get_session, mock_update_stock, mock_send_alert
):
    # Test non-deduct operation (e.g., "add") where no stock alert is sent.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    updated_item = {"id": 3, "quantity": 20}
    mock_update_stock.return_value = updated_item

    event = {
        "data": {
            "response_body": {
                "items": [
                    {"item_id": "item3", "location_id": "loc3", "quantity": 30}
                ]
            },
            "operation": "add",
        }
    }
    context = {}
    response = lambda_handler(event, context)

    assert response["statusCode"] == 201
    # No reservation_id or purchase_id included.
    assert "reservation_id" not in response
    assert "purchase_id" not in response
    assert response["updated_items"] == [updated_item]

    # For non-deduct operations, no alert is sent.
    mock_send_alert.assert_not_called()

    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()


def test_lambda_handler_no_items():
    # Test that if no items are provided in the event input, a ValueError is raised.
    event = {"data": {"response_body": {}}}  # "items" key missing
    context = {}
    with pytest.raises(ValueError) as excinfo:
        lambda_handler(event, context)
    assert "No items provided in the event input." in str(excinfo.value)
