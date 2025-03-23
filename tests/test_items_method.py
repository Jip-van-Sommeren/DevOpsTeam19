import json
from unittest.mock import patch, MagicMock
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "python"))

from src.items_method import lambda_handler


@patch("src.items_method.generate_presigned_url")
@patch("src.items_method.get_session")
def test_get_items(mock_get_session, mock_generate_presigned_url):
    """
    Test the GET /items path to ensure it returns
    a list of items correctly.
    """

    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_item = MagicMock()
    mock_item.id = 1
    mock_item.name = "Test Item"
    mock_item.description = "A test item"
    mock_item.price = 9.99
    mock_item.s3_key = "test-image.png"

    mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [
        mock_item
    ]

    mock_generate_presigned_url.return_value = "https://mocked_s3_url"

    event = {
        "httpMethod": "GET",
        "resource": "/items",
        "queryStringParameters": {"skip": "0", "limit": "10"},
    }
    context = {}

    response = lambda_handler(event, context)

    assert response["statusCode"] == 200
    assert "body" in response

    items = json.loads(response["body"])
    assert len(items) == 1

    first_item = items[0]
    assert first_item["id"] == 1
    assert first_item["name"] == "Test Item"
    assert first_item["price"] == 9.99
    assert first_item["image_url"] == "https://mocked_s3_url"

    mock_session.close.assert_called_once()
