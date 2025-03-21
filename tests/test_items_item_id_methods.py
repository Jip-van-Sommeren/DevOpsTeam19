import json
import os
from unittest.mock import MagicMock, patch

# Ensure S3_BUCKET is set for tests.
os.environ["S3_BUCKET"] = "test-bucket"

# Import the lambda handler from your module.
from src.items_item_id_methods import lambda_handler


# -----------------------------------------------------------------------------
# Helper: Create a fake item object (simulate an ORM model instance)
# -----------------------------------------------------------------------------
def create_fake_item():
    fake_item = MagicMock()
    fake_item.id = 1
    fake_item.name = "Test Item"
    fake_item.description = "A test item"
    fake_item.price = 100
    fake_item.s3_key = "test-key"
    return fake_item


# -----------------------------------------------------------------------------
# Tests for missing item_id in pathParameters
# -----------------------------------------------------------------------------
def test_lambda_handler_missing_item_id():
    event = {"httpMethod": "GET", "pathParameters": {}}  # missing "item_id"
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing item_id in path" in body["message"]


# -----------------------------------------------------------------------------
# Tests for GET method (get_item)
# -----------------------------------------------------------------------------
@patch("src.items_item_id_methods.generate_presigned_url")
@patch("src.items_item_id_methods.get_session")
def test_get_item_found(mock_get_session, mock_generate_presigned_url):
    # Arrange
    fake_item = create_fake_item()
    # When get_session() is called, return a fake session with a query chain.
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_item
    )
    mock_get_session.return_value = fake_session
    # Let generate_presigned_url return a mocked URL.
    mock_generate_presigned_url.return_value = "https://example.com/test-key"

    event = {"httpMethod": "GET", "pathParameters": {"item_id": "1"}}
    context = {}

    # Act
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 200
    # Parse body and validate fields.
    body = json.loads(response["body"])
    assert body["id"] == fake_item.id
    assert body["name"] == fake_item.name
    assert body["description"] == fake_item.description
    assert body["price"] == fake_item.price
    assert body["image_url"] == "https://example.com/test-key"
    fake_session.close.assert_called_once()


@patch("src.items_item_id_methods.get_session")
def test_get_item_not_found(mock_get_session):
    # Arrange: simulate query returning None.
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    event = {
        "httpMethod": "GET",
        "pathParameters": {"item_id": "999"},  # non-existent item
    }
    context = {}

    # Act
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Item not found" in body["message"]
    fake_session.close.assert_called_once()


# -----------------------------------------------------------------------------
# Tests for DELETE method (delete_item)
# -----------------------------------------------------------------------------
@patch("src.items_item_id_methods.get_session")
def test_delete_item_not_found(mock_get_session):
    # Arrange: simulate no item found.
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "DELETE", "pathParameters": {"item_id": "999"}}
    context = {}

    # Act
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Item not found" in body["message"]
    fake_session.close.assert_called_once()


@patch("src.items_item_id_methods.get_session")
def test_delete_item_success(mock_get_session):
    # Arrange: simulate item exists.
    fake_item = create_fake_item()
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_item
    )
    mock_get_session.return_value = fake_session

    event = {"httpMethod": "DELETE", "pathParameters": {"item_id": "1"}}
    context = {}

    # Act
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    # Check that the returned body includes id, name, description.
    assert body["id"] == fake_item.id
    assert body["name"] == fake_item.name
    assert body["description"] == fake_item.description
    fake_session.delete.assert_called_once_with(fake_item)
    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()


# -----------------------------------------------------------------------------
# Tests for PUT method (update_item)
# -----------------------------------------------------------------------------
@patch("src.items_item_id_methods.get_session")
def test_update_item_invalid_json(mock_get_session):
    # Test that if the PUT body contains invalid JSON, a 400 is returned.
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"item_id": "1"},
        "body": "not a json",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["message"]


@patch("src.items_item_id_methods.get_session")
def test_update_item_not_found(mock_get_session):
    # Arrange: simulate no item found.
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    payload = {"name": "Updated Name", "description": "Updated Desc"}
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps(payload),
    }
    context = {}

    # Act
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Item not found" in body["message"]
    fake_session.close.assert_called_once()


@patch("src.items_item_id_methods.get_session")
def test_update_item_success(mock_get_session):
    # Arrange: simulate item exists.
    fake_item = create_fake_item()
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_item
    )
    mock_get_session.return_value = fake_session

    payload = {"name": "Updated Name", "description": "Updated Desc"}
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"item_id": "1"},
        "body": json.dumps(payload),
    }
    context = {}

    # Act
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    # The update_item function should update the fake_item's name and description.
    assert body["id"] == fake_item.id
    assert body["name"] == "Updated Name"
    assert body["description"] == "Updated Desc"
    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once_with(fake_item)
    fake_session.close.assert_called_once()


# -----------------------------------------------------------------------------
# Test for unsupported HTTP method
# -----------------------------------------------------------------------------
def test_method_not_allowed():
    event = {
        "httpMethod": "PATCH",  # unsupported method
        "pathParameters": {"item_id": "1"},
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert "Method PATCH not allowed" in body["message"]
