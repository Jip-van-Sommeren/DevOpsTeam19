import pytest
from unittest.mock import MagicMock, patch
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the project root so that "src" can be imported.
sys.path.insert(0, project_root)

# Add the "python" folder so that the layer code (e.g. db_layer) can be found.
sys.path.insert(0, os.path.join(project_root, "python"))
# Import the lambda_handler from your check_reservation module.
from src.check_reservation import lambda_handler


def test_missing_reservation_id():
    # Test that if reservation_id is missing, the handler raises a ValueError.
    event = {"data": {}}  # No reservation_id provided.
    context = {}

    with pytest.raises(ValueError) as excinfo:
        lambda_handler(event, context)
    assert "Missing reservation_id" in str(excinfo.value)


@patch("src.check_reservation.get_session")
def test_reservation_exists(mock_get_session):
    # Create a fake session and configure its query chain.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    # Create a fake reservation object (its mere existence is enough).
    fake_reservation = MagicMock()
    fake_reservation.id = 123

    # Simulate session.query(Reservation).filter(...).first() returning our fake reservation.
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_reservation
    )

    # Create an event with a reservation_id and a response_body containing items.
    event = {
        "data": {
            "reservation_id": 123,
            "response_body": {"items": ["item1", "item2"]},
        }
    }
    context = {}

    result = lambda_handler(event, context)
    assert result["reservationExists"] is True
    assert result["stock_operation"] == "add"
    assert result["items"] == ["item1", "item2"]
    # Ensure the session is closed.
    fake_session.close.assert_called_once()


@patch("src.check_reservation.get_session")
def test_reservation_not_exists(mock_get_session):
    # Create a fake session where the query returns None.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    # Simulate session.query(Reservation).filter(...).first() returning None.
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )

    event = {"data": {"reservation_id": 456}}
    context = {}

    result = lambda_handler(event, context)
    # Expect a response indicating that the reservation does not exist.
    assert result["reservationExists"] is False
    # Verify that the session was closed.
    fake_session.close.assert_called_once()
