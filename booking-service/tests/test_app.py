import pytest
from unittest.mock import patch
from datetime import datetime

def make_booking_data(user_id=1, flight_id=1, seat_number=1):
    return {
        "user_id": user_id,
        "flight_id": flight_id,
        "seat_number": seat_number
    }

def test_create_booking(client):
    booking_data = make_booking_data()
    with patch("app.get_flight_info", return_value={"available_seats": 10, "price": 100.0}), \
         patch("app.lock_seat", return_value=True), \
         patch("app.release_seat_lock", return_value=None), \
         patch("app.get_user_info", return_value={"id": 1, "email": "test@example.com"}), \
         patch("app.requests.put", return_value=type("obj", (object,), {"status_code": 200})()):
        response = client.post("/bookings", json=booking_data)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == booking_data["user_id"]
        assert data["flight_id"] == booking_data["flight_id"]
        assert data["seat_number"] == booking_data["seat_number"]
        assert data["status"] == "pending"
        assert data["id"]
        assert data["booking_date"]

def test_get_bookings(client):
    with patch("app.get_flight_info", return_value={"available_seats": 10, "price": 100.0}), \
         patch("app.lock_seat", return_value=True), \
         patch("app.release_seat_lock", return_value=None), \
         patch("app.get_user_info", return_value={"id": 2, "email": "test2@example.com"}), \
         patch("app.requests.put", return_value=type("obj", (object,), {"status_code": 200})()):
        client.post("/bookings", json=make_booking_data(user_id=2, flight_id=2, seat_number=2))
    response = client.get("/bookings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_booking_by_id_success(client):
    with patch("app.get_flight_info", return_value={"available_seats": 10, "price": 100.0}), \
         patch("app.lock_seat", return_value=True), \
         patch("app.release_seat_lock", return_value=None), \
         patch("app.get_user_info", return_value={"id": 3, "email": "test3@example.com"}), \
         patch("app.requests.put", return_value=type("obj", (object,), {"status_code": 200})()):
        post_resp = client.post("/bookings", json=make_booking_data(user_id=3, flight_id=3, seat_number=3))
    booking_id = post_resp.json()["id"]
    response = client.get(f"/bookings/{booking_id}")
    assert response.status_code == 200
    assert response.json()["id"] == booking_id

def test_get_booking_by_id_not_found(client):
    response = client.get("/bookings/99999")
    assert response.status_code == 404
    assert "Booking not found" in response.json()["detail"]

def test_cancel_booking_success(client):
    with patch("app.get_flight_info", return_value={"available_seats": 10, "price": 100.0}), \
         patch("app.lock_seat", return_value=True), \
         patch("app.release_seat_lock", return_value=None), \
         patch("app.get_user_info", return_value={"id": 4, "email": "test4@example.com"}), \
         patch("app.requests.put", return_value=type("obj", (object,), {"status_code": 200})()):
        post_resp = client.post("/bookings", json=make_booking_data(user_id=4, flight_id=4, seat_number=4))
    booking_id = post_resp.json()["id"]
    with patch("app.release_seat_lock", return_value=None), \
         patch("app.get_flight_info", return_value={"available_seats": 10, "price": 100.0}), \
         patch("app.requests.put", return_value=type("obj", (object,), {"status_code": 200})()):
        response = client.put(f"/bookings/{booking_id}/cancel")
    assert response.status_code == 200
    assert response.json()["message"] == "Booking cancelled successfully"

def test_cancel_booking_not_found(client):
    response = client.put("/bookings/99999/cancel")
    assert response.status_code == 404
    assert "Booking not found" in response.json()["detail"]

def test_get_booking_status_success(client):
    with patch("app.get_flight_info", return_value={"available_seats": 10, "price": 100.0}), \
         patch("app.lock_seat", return_value=True), \
         patch("app.release_seat_lock", return_value=None), \
         patch("app.get_user_info", return_value={"id": 5, "email": "test5@example.com"}), \
         patch("app.requests.put", return_value=type("obj", (object,), {"status_code": 200})()):
        post_resp = client.post("/bookings", json=make_booking_data(user_id=5, flight_id=5, seat_number=5))
    booking_id = post_resp.json()["id"]
    response = client.get(f"/bookings/{booking_id}/status")
    assert response.status_code == 200
    assert "status" in response.json()

def test_get_booking_status_not_found(client):
    response = client.get("/bookings/99999/status")
    assert response.status_code == 404
    assert "Booking not found" in response.json()["detail"] 