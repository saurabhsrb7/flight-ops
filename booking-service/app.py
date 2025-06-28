from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import requests
import redis
import json

from database import get_db, engine
from models import Base, Booking
from schemas import BookingCreate, BookingResponse, BookingStatus
from tasks import process_payment_task, send_notification_task

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logger = structlog.get_logger()

# Redis for seat locking
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
BOOKING_COUNT = Counter('bookings_total', 'Total bookings', ['status'])

app = FastAPI(title="Booking Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
FLIGHT_SERVICE_URL = "http://localhost:8001"
USER_SERVICE_URL = "http://localhost:8000"
PAYMENT_SERVICE_URL = "http://localhost:8003"

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    duration = (datetime.now() - start_time).total_seconds()
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.observe(duration)
    
    logger.info(
        "Request processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    return response

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "booking-service"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def get_flight_info(flight_id: int):
    """Get flight information from flight service"""
    try:
        response = requests.get(f"{FLIGHT_SERVICE_URL}/flights/{flight_id}")
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flight not found"
            )
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flight service unavailable"
        )

def get_user_info(user_id: int):
    """Get user information from user service"""
    try:
        response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User service unavailable"
        )

def lock_seat(flight_id: int, seat_number: int, user_id: int) -> bool:
    """Lock a seat using Redis for concurrency control"""
    lock_key = f"seat_lock:{flight_id}:{seat_number}"
    lock_value = str(user_id)
    
    # Try to acquire lock with expiration
    if redis_client.set(lock_key, lock_value, ex=300, nx=True):  # 5 minutes expiration
        return True
    return False

def release_seat_lock(flight_id: int, seat_number: int):
    """Release seat lock"""
    lock_key = f"seat_lock:{flight_id}:{seat_number}"
    redis_client.delete(lock_key)

@app.post("/bookings", response_model=BookingResponse)
async def create_booking(
    booking: BookingCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new booking with seat locking"""
    # Get flight information
    flight_info = get_flight_info(booking.flight_id)
    
    # Check if seat is available
    if flight_info["available_seats"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No seats available"
        )
    
    # Try to lock the seat
    if not lock_seat(booking.flight_id, booking.seat_number, booking.user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seat is already locked or booked"
        )
    
    try:
        # Create booking
        db_booking = Booking(
            user_id=booking.user_id,
            flight_id=booking.flight_id,
            seat_number=booking.seat_number,
            booking_date=datetime.now(),
            status=BookingStatus.PENDING,
            total_amount=flight_info["price"]
        )
        
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        
        # Update flight available seats
        flight_response = requests.put(
            f"{FLIGHT_SERVICE_URL}/flights/{booking.flight_id}",
            json={"available_seats": flight_info["available_seats"] - 1}
        )
        
        if flight_response.status_code != 200:
            # Rollback booking if flight update fails
            db.delete(db_booking)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update flight seats"
            )
        
        # Add background tasks
        background_tasks.add_task(process_payment_task, db_booking.id)
        background_tasks.add_task(send_notification_task, db_booking.id)
        
        BOOKING_COUNT.labels(status="created").inc()
        logger.info("Booking created", booking_id=db_booking.id, user_id=booking.user_id)
        
        return BookingResponse.from_orm(db_booking)
        
    except Exception as e:
        # Release seat lock on error
        release_seat_lock(booking.flight_id, booking.seat_number)
        raise e

@app.get("/bookings", response_model=List[BookingResponse])
async def get_bookings(
    user_id: int = None,
    flight_id: int = None,
    status: BookingStatus = None,
    db: Session = Depends(get_db)
):
    """Get bookings with optional filtering"""
    query = db.query(Booking)
    
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    if flight_id:
        query = query.filter(Booking.flight_id == flight_id)
    if status:
        query = query.filter(Booking.status == status)
    
    bookings = query.all()
    return [BookingResponse.from_orm(booking) for booking in bookings]

@app.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Get a specific booking by ID"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return BookingResponse.from_orm(booking)

@app.put("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    """Cancel a booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled"
        )
    
    # Update booking status
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now()
    
    # Release seat lock
    release_seat_lock(booking.flight_id, booking.seat_number)
    
    # Update flight available seats
    flight_info = get_flight_info(booking.flight_id)
    requests.put(
        f"{FLIGHT_SERVICE_URL}/flights/{booking.flight_id}",
        json={"available_seats": flight_info["available_seats"] + 1}
    )
    
    db.commit()
    
    BOOKING_COUNT.labels(status="cancelled").inc()
    logger.info("Booking cancelled", booking_id=booking_id)
    
    return {"message": "Booking cancelled successfully"}

@app.get("/bookings/{booking_id}/status")
async def get_booking_status(booking_id: int, db: Session = Depends(get_db)):
    """Get booking status"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return {"booking_id": booking_id, "status": booking.status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 