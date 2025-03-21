import os
import base64
from unittest.mock import MagicMock, patch

# Ensure S3_BUCKET is set for testing.
os.environ["S3_BUCKET"] = "test-bucket"

# Import the Lambda handler and add_items function from your module.
from src.items_post import lambda_handler


def test_lambda_handler_invalid_items():
    """
    Verify that if 'items' is not a list, the Lambda returns a 400 error.
    """
    event = {"data": {"items": "not a list"}}
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = response["body"]
    # The handler returns a dict in body for this error.
    assert "Expected 'items' to be a list" in body["error"]


@patch("src.items_post.get_session")
@patch("src.items_post.s3_client.put_object")
@patch("src.items_post.uuid.uuid4")
@patch("src.items_post.Item")
def test_lambda_handler_success(
    mock_Item, mock_uuid, mock_put_object, mock_get_session
):
    """
    Test a successful call to the Lambda with a valid list of items.

    The input list contains:
      - One item without image_data.
      - One item with image_data.

    The test verifies:
      - The S3 client is called for the item with image_data.
      - The DB session's commit, refresh, and close methods are called.
      - The Lambda returns a 201 response with an 'added_items' list.
    """
    # Arrange
    # Patch uuid.uuid4 to return a fixed hex value.
    fake_uuid_obj = MagicMock()
    fake_uuid_obj.hex = "fakehex"
    mock_uuid.return_value = fake_uuid_obj

    # Prepare a fake DB session.
    fake_session = MagicMock()
    mock_get_session.return_value = fake_session

    # Create two fake item instances that will be returned by the patched Item constructor.
    fake_item_without = MagicMock()
    fake_item_without.id = 1
    fake_item_without.name = "Item A"
    fake_item_without.description = ["description"]
    fake_item_without.price = 50

    fake_item_with = MagicMock()
    fake_item_with.id = 2
    fake_item_with.name = "Item B"
    fake_item_with.description = "Desc B"
    fake_item_with.price = 100
    # After processing, s3_key is assigned.
    fake_item_with.s3_key = "items/item_fakehex.jpg"

    # Configure the Item constructor to return our fake items in order.
    mock_Item.side_effect = [fake_item_without, fake_item_with]

    # Define two test items:
    # - First item has no image_data.
    item1 = {"name": "Item A", "price": 50}
    # - Second item includes description and base64-encoded image_data.
    #    base64.b64decode("dGVzdA==") decodes to b"test".
    item2 = {
        "name": "Item B",
        "price": 100,
        "description": "Desc B",
        "image_data": "dGVzdA==",
    }
    items_list = [item1, item2]

    # Build the event as expected by the Lambda handler.
    event = {"data": {"items": items_list}}
    context = {}

    # Act
    response = lambda_handler(event, context)

    # Assert
    # The Lambda should return a 201 status with an 'added_items' list.
    assert response["statusCode"] == 201
    added_items = response["added_items"]
    assert len(added_items) == 2

    # Verify the response for the first item (without image_data).
    resp_item1 = added_items[0]
    assert resp_item1["id"] == fake_item_without.id
    assert resp_item1["name"] == fake_item_without.name
    assert resp_item1["description"] == fake_item_without.description
    assert resp_item1["price"] == fake_item_without.price
    assert "s3_key" not in resp_item1

    # Verify the response for the second item (with image_data).
    resp_item2 = added_items[1]
    assert resp_item2["id"] == fake_item_with.id
    assert resp_item2["name"] == fake_item_with.name
    assert resp_item2["description"] == fake_item_with.description
    assert resp_item2["price"] == fake_item_with.price
    assert resp_item2["s3_key"] == "items/item_fakehex.jpg"

    # Verify that S3 put_object was called once for the second item.
    mock_put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="items/item_fakehex.jpg",
        Body=base64.b64decode("dGVzdA=="),
        ContentType="image/jpeg",
    )

    # Verify session methods:
    # Since we process two items, commit and refresh should be called twice.
    assert fake_session.commit.call_count == 2
    assert fake_session.refresh.call_count == 2
    fake_session.close.assert_called_once()
