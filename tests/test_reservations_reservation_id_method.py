import json
import datetime
from unittest.mock import MagicMock, patch

from src.reservations_reservation_id_method import (
    lambda_handler,
    get_reservation,
    delete_reservation,
    update_reservation,
)


# Helper functions to create fake objects.
def create_fake_reservation(res_id=1, user_id=100, status="reserved"):
    fake = MagicMock()
    fake.id = res_id
    fake.user_id = user_id
    fake.status = status
    fake.created_at = datetime.datetime(2023, 1, 1, 12, 0, 0)
    fake.updated_at = datetime.datetime(2023, 1, 2, 12, 0, 0)
    return fake


def create_fake_reserved_item(item_id, quantity):
    fake = MagicMock()
    fake.item_id = item_id
    fake.quantity = quantity
    return fake


# ---------------------------------------------------------------------------
# Test: Missing reservation_id in path parameters.
# ---------------------------------------------------------------------------
def test_lambda_handler_missing_reservation_id():
    event = {
        "httpMethod": "GET",
        "pathParameters": {},  # No reservation_id provided.
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing reservation_id in path" in body["message"]


# ---------------------------------------------------------------------------
# GET: Reservation not found.
# ---------------------------------------------------------------------------
@patch("src.reservations_reservation_id_method.get_session")
def test_get_reservation_not_found(mock_get_session):
    fake_session = MagicMock()
    # For the first query (for Reservation), return None.
    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = None
    fake_session.query.return_value = fake_query
    mock_get_session.return_value = fake_session

    response = get_reservation("999")
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Reservation not found" in body["message"]
    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# GET: Reservation found.
# ---------------------------------------------------------------------------
@patch("src.reservations_reservation_id_method.get_session")
def test_get_reservation_found(mock_get_session):
    # Create a fake reservation.
    fake_res = create_fake_reservation(1, 100, "reserved")
    # Create a fake reserved item.
    fake_reserved_item = create_fake_reserved_item(10, 2)

    fake_session = MagicMock()
    fake_query_res = MagicMock()
    fake_query_res.filter.return_value.first.return_value = fake_res
    fake_query_items = MagicMock()
    fake_query_items.filter.return_value.all.return_value = [
        fake_reserved_item
    ]
    fake_session.query.side_effect = [fake_query_res, fake_query_items]
    mock_get_session.return_value = fake_session

    response = get_reservation("1")
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body = json.loads(response["body"])
    assert body["id"] == fake_res.id
    assert body["user_id"] == fake_res.user_id
    assert body["status"] == fake_res.status
    assert body["created_at"] == fake_res.created_at.isoformat()
    assert body["updated_at"] == fake_res.updated_at.isoformat()
    # Check reserved items.
    assert isinstance(body["reserved_items"], list)
    assert len(body["reserved_items"]) == 1
    assert body["reserved_items"][0]["item_id"] == fake_reserved_item.item_id
    assert body["reserved_items"][0]["quantity"] == fake_reserved_item.quantity

    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# DELETE: Reservation not found.
# ---------------------------------------------------------------------------
@patch("src.reservations_reservation_id_method.get_session")
def test_delete_reservation_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    response = delete_reservation("999")
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Reservation not found" in body["message"]
    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# DELETE: Reservation found.
# ---------------------------------------------------------------------------
@patch("src.reservations_reservation_id_method.get_session")
def test_delete_reservation_found(mock_get_session):
    fake_res = create_fake_reservation(2, 200, "reserved")
    fake_session = MagicMock()
    # For DELETE, first query returns the reservation.
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_res
    )
    mock_get_session.return_value = fake_session

    response = delete_reservation("2")
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body = json.loads(response["body"])
    assert "Reservation deleted" in body["message"]
    assert body["reservation"]["id"] == fake_res.id
    assert body["reservation"]["user_id"] == fake_res.user_id
    assert body["reservation"]["status"] == fake_res.status

    fake_session.delete.assert_called_once_with(fake_res)
    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# PUT: Invalid JSON.
# ---------------------------------------------------------------------------
def test_update_reservation_invalid_json():
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"reservation_id": "1"},
        "body": "invalid json",
    }
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["message"]


# ---------------------------------------------------------------------------
# PUT: Reservation not found.
# ---------------------------------------------------------------------------
@patch("src.reservations_reservation_id_method.get_session")
def test_update_reservation_not_found(mock_get_session):
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        None
    )
    mock_get_session.return_value = fake_session

    payload = {"user_id": 300, "status": "completed"}
    response = update_reservation("1", payload)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Reservation not found" in body["message"]
    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# PUT: Successful update.
# ---------------------------------------------------------------------------
@patch("src.reservations_reservation_id_method.get_session")
def test_update_reservation_success(mock_get_session):
    fake_res = create_fake_reservation(3, 350, "pending")
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = (
        fake_res
    )
    mock_get_session.return_value = fake_session

    # Prepare payload for update.
    payload = {"user_id": 400, "status": "confirmed"}
    response = update_reservation("3", payload)
    assert response["statusCode"] == 200
    headers = response.get("headers", {})
    assert headers.get("Content-Type") == "application/json"
    body_resp = json.loads(response["body"])
    assert body_resp["id"] == fake_res.id
    assert body_resp["user_id"] == payload["user_id"]
    assert body_resp["status"] == payload["status"]
    assert body_resp["created_at"] == fake_res.created_at.isoformat()
    assert body_resp["updated_at"] == fake_res.updated_at.isoformat()
    fake_session.commit.assert_called_once()
    fake_session.refresh.assert_called_once_with(fake_res)
    fake_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# Test: Unsupported HTTP method.
# ---------------------------------------------------------------------------
def test_lambda_handler_method_not_allowed():
    event = {"httpMethod": "PATCH", "pathParameters": {"reservation_id": "1"}}
    context = {}
    response = lambda_handler(event, context)
    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert "Method PATCH not allowed" in body["message"]
