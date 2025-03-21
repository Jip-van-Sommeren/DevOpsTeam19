import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Import your handler
# Adjust the path if needed, e.g. if it's src/items_method.py:


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the project root so that "src" can be imported.
sys.path.insert(0, project_root)

# Add the "python" folder so that the layer code (e.g. db_layer) can be found.
sys.path.insert(0, os.path.join(project_root, "python"))


from src.items_method import lambda_handler


@patch("src.items_method.generate_presigned_url")
@patch("src.items_method.get_session")
def test_get_items(mock_get_session, mock_generate_presigned_url):
    """
    Test the GET /items path to ensure it returns
    a list of items correctly.
    """

    # 1. SETUP MOCKS

    # Mock a database session
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    # Mock a single 'Item' record (you can create multiple if you want)
    mock_item = MagicMock()
    mock_item.id = 1
    mock_item.name = "Test Item"
    mock_item.description = "A test item"
    mock_item.price = 9.99
    mock_item.s3_key = "test-image.png"

    # Configure the query chain to return a list with our mock item
    mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [
        mock_item
    ]

    # Mock the presigned URL generation
    mock_generate_presigned_url.return_value = "https://mocked_s3_url"

    # 2. CREATE EVENT
    # This simulates an API Gateway event calling GET /items?skip=0&limit=10
    event = {
        "httpMethod": "GET",
        "resource": "/items",
        "queryStringParameters": {"skip": "0", "limit": "10"},
    }
    context = {}

    # 3. INVOKE THE HANDLER
    response = lambda_handler(event, context)

    # 4. ASSERT THE RESULT
    assert response["statusCode"] == 200
    assert "body" in response

    # Parse the JSON body
    items = json.loads(response["body"])
    assert len(items) == 1

    # Verify the item fields
    first_item = items[0]
    assert first_item["id"] == 1
    assert first_item["name"] == "Test Item"
    assert first_item["price"] == 9.99
    assert first_item["image_url"] == "https://mocked_s3_url"

    # 5. CHECK THAT THE SESSION WAS CLOSED
    mock_session.close.assert_called_once()
