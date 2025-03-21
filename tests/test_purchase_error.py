from unittest.mock import MagicMock, patch

# Import the lambda_handler from your module.
from src.purchase_error import lambda_handler


def test_lambda_handler_no_purchase_id():
    """
    Test that if no purchase_id is provided in the event data,
    the Lambda returns a 400 response.
    """
    event = {"data": {}}  # purchase_id missing
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    # The body is returned as a dict.
    assert response["body"]["message"] == "No purchase_id provided"


@patch("src.purchase_error.get_session")
def test_lambda_handler_cancel_success(mock_get_session):
    """
    Test that a valid purchase_id triggers cancellation and returns a 200 response.
    This test patches get_session to simulate database operations.
    """
    # Arrange: Create a fake session object.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    # --- Simulate deletion of purchased items ---
    # When deleting purchased items, the code calls:
    # session.query(PurchasedItem).filter(...).delete()
    fake_query = MagicMock()
    fake_session.query.return_value.filter.return_value = fake_query
    fake_query.delete.return_value = None

    # --- Simulate retrieving the Purchase record ---
    # To test deletion, we simulate that a purchase is found.
    fake_purchase = MagicMock()
    fake_purchase.id = 42
    # We set up the chain for retrieving the purchase record.
    # Note: The same session.query(...).filter(...) chain is used in both deletion calls.
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_purchase
    )

    # Build the event with a valid purchase_id.
    event = {"data": {"purchase_id": 42}}
    context = {}

    # Act: Invoke the lambda handler.
    response = lambda_handler(event, context)

    # Assert: Verify that the cancellation succeeded.
    assert response["statusCode"] == 200
    assert response["body"]["message"] == "Purchase 42 cancelled successfully."

    # Verify that the session methods were called:
    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()
