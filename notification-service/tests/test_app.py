import pytest
from unittest.mock import patch
from datetime import datetime

def make_notification_data(user_id=1, booking_id=1, flight_id=1, status="confirmed", amount=100.0):
    return {
        "user_id": user_id,
        "booking_id": booking_id,
        "flight_id": flight_id,
        "status": status,
        "amount": amount
    }

def test_create_notification(client):
    notification_data = make_notification_data()
    with patch("app.get_user_email", return_value="test@example.com"), \
         patch("app.get_flight_details", return_value={"flight_number": "AI101", "origin": "DEL", "destination": "BOM"}), \
         patch("app.send_email_notification", return_value=True):
        response = client.post("/notifications", json=notification_data)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == notification_data["user_id"]
        assert data["booking_id"] == notification_data["booking_id"]
        assert data["message"].startswith("Booking")
        assert data["id"]
        assert data["sent_at"]

def test_get_notifications(client):
    with patch("app.get_user_email", return_value="test@example.com"), \
         patch("app.get_flight_details", return_value={"flight_number": "AI101", "origin": "DEL", "destination": "BOM"}), \
         patch("app.send_email_notification", return_value=True):
        client.post("/notifications", json=make_notification_data(user_id=2, booking_id=2, flight_id=2))
    response = client.get("/notifications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_notification_by_id_success(client):
    with patch("app.get_user_email", return_value="test@example.com"), \
         patch("app.get_flight_details", return_value={"flight_number": "AI101", "origin": "DEL", "destination": "BOM"}), \
         patch("app.send_email_notification", return_value=True):
        post_resp = client.post("/notifications", json=make_notification_data(user_id=3, booking_id=3, flight_id=3))
    notification_id = post_resp.json()["id"]
    response = client.get(f"/notifications/{notification_id}")
    assert response.status_code == 200
    assert response.json()["id"] == notification_id

def test_get_notification_by_id_not_found(client):
    response = client.get("/notifications/99999")
    assert response.status_code == 404
    assert "Notification not found" in response.json()["detail"]

def test_resend_notification_success(client):
    with patch("app.get_user_email", return_value="test@example.com"), \
         patch("app.get_flight_details", return_value={"flight_number": "AI101", "origin": "DEL", "destination": "BOM"}), \
         patch("app.send_email_notification", return_value=True):
        post_resp = client.post("/notifications", json=make_notification_data(user_id=4, booking_id=4, flight_id=4))
    notification_id = post_resp.json()["id"]
    with patch("app.get_user_email", return_value="test@example.com"), \
         patch("app.send_email_notification", return_value=True):
        response = client.post(f"/notifications/{notification_id}/resend")
        assert response.status_code == 200 or response.status_code == 204

def test_resend_notification_not_found(client):
    response = client.post("/notifications/99999/resend")
    assert response.status_code == 404
    assert "Notification not found" in response.json()["detail"] 