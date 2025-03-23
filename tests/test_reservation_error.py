from unittest.mock import MagicMock, patch
from src.reservation_error import lambda_handler


def test_lambda_handler_no_reservation_id():
    """
    Test that if no reservation_id is provided in the event data,
    the Lambda returns a 400 response.
    """
    event = {"data": {}}  # reservation_id missing
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    assert response["body"]["message"] == "No reservation_id provided"


@patch("src.reservation_error.get_session")
def test_lambda_handler_cancel_success(mock_get_session):
    """
    Test that a valid reservation_id triggers cancellation and returns a 200
    response.
    This test patches get_session to simulate database operations.
    """
    # Arrange: Create a fake session object.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    fake_query = MagicMock()
    fake_session.query.return_value.filter.return_value = fake_query
    fake_query.delete.return_value = None

    fake_reservation = MagicMock()
    fake_reservation.id = 42
    # We set up the chain for retrieving the reservation record.
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_reservation
    )

    event = {"data": {"reservation_id": 42}}
    context = {}

    response = lambda_handler(event, context)

    assert response["statusCode"] == 200
    assert (
        response["body"]["message"] == "Reservation 42 cancelled successfully."
    )

    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()
