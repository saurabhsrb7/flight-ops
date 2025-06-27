import pytest
from datetime import datetime, timedelta

# Helper to generate flight data
def make_flight_data(
    flight_number="FL123",
    airline="Test Airline",
    origin="NYC",
    destination="LAX",
    departure_time=None,
    arrival_time=None,
    total_seats=150,
    available_seats=150,
    price=299.99
):
    if departure_time is None:
        departure_time = (datetime.now() + timedelta(days=1)).replace(microsecond=0).isoformat()
    if arrival_time is None:
        arrival_time = (datetime.now() + timedelta(days=1, hours=5)).replace(microsecond=0).isoformat()
    return {
        "flight_number": flight_number,
        "airline": airline,
        "origin": origin,
        "destination": destination,
        "departure_time": departure_time,
        "arrival_time": arrival_time,
        "total_seats": total_seats,
        "available_seats": available_seats,
        "price": price
    }

def test_create_flight(client):
    flight_data = make_flight_data()
    response = client.post("/flights", json=flight_data)
    assert response.status_code == 200
    data = response.json()
    for key in flight_data:
        assert data[key] == flight_data[key]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data

def test_get_flights(client):
    # Create two flights
    client.post("/flights", json=make_flight_data(flight_number="FL1"))
    client.post("/flights", json=make_flight_data(flight_number="FL2"))
    response = client.get("/flights")
    assert response.status_code == 200
    flights = response.json()
    assert len(flights) >= 2
    numbers = [f["flight_number"] for f in flights]
    assert "FL1" in numbers and "FL2" in numbers

def test_search_flights(client):
    # Create a flight for search
    dep_date = (datetime.now() + timedelta(days=2)).date().isoformat()
    flight_data = make_flight_data(
        flight_number="SEARCH1",
        origin="BOS",
        destination="SFO",
        departure_time=f"{dep_date}T08:00:00",
        arrival_time=f"{dep_date}T12:00:00"
    )
    client.post("/flights", json=flight_data)
    # Search
    response = client.get(f"/flights/search?origin=BOS&destination=SFO&departure_date={dep_date}")
    assert response.status_code == 200
    results = response.json()
    assert any(f["flight_number"] == "SEARCH1" for f in results)

def test_search_flights_invalid_date(client):
    response = client.get("/flights/search?origin=BOS&destination=SFO&departure_date=bad-date")
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]

def test_get_flight_by_id_success(client):
    flight_data = make_flight_data(flight_number="BYID1")
    post_resp = client.post("/flights", json=flight_data)
    flight_id = post_resp.json()["id"]
    response = client.get(f"/flights/{flight_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["flight_number"] == "BYID1"

def test_get_flight_by_id_not_found(client):
    response = client.get("/flights/99999")
    assert response.status_code == 404
    assert "Flight not found" in response.json()["detail"]

def test_update_flight_success(client):
    flight_data = make_flight_data(flight_number="UPD1")
    post_resp = client.post("/flights", json=flight_data)
    flight_id = post_resp.json()["id"]
    update_data = {"price": 199.99, "available_seats": 100}
    response = client.put(f"/flights/{flight_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 199.99
    assert data["available_seats"] == 100

def test_update_flight_not_found(client):
    update_data = {"price": 199.99}
    response = client.put("/flights/99999", json=update_data)
    assert response.status_code == 404
    assert "Flight not found" in response.json()["detail"]

def test_delete_flight_success(client):
    flight_data = make_flight_data(flight_number="DEL1")
    post_resp = client.post("/flights", json=flight_data)
    flight_id = post_resp.json()["id"]
    response = client.delete(f"/flights/{flight_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Flight deleted successfully"
    # Confirm deletion
    get_resp = client.get(f"/flights/{flight_id}")
    assert get_resp.status_code == 404

def test_delete_flight_not_found(client):
    response = client.delete("/flights/99999")
    assert response.status_code == 404
    assert "Flight not found" in response.json()["detail"]

def test_create_flight_missing_fields(client):
    # Missing required field: flight_number
    flight_data = make_flight_data()
    del flight_data["flight_number"]
    response = client.post("/flights", json=flight_data)
    assert response.status_code == 422

def test_create_flight_invalid_price(client):
    flight_data = make_flight_data(price="not-a-float")
    response = client.post("/flights", json=flight_data)
    assert response.status_code == 422 