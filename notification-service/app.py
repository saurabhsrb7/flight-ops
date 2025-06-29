from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import requests

from database import get_db, engine
from models import Base, Notification
from schemas import NotificationCreate, NotificationResponse, NotificationType
from email_service import send_email_notification

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
NOTIFICATION_COUNT = Counter('notifications_total', 'Total notifications', ['type', 'status'])

app = FastAPI(title="Notification Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
USER_SERVICE_URL = "http://localhost:8000"
FLIGHT_SERVICE_URL = "http://localhost:8001"

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
    return {"status": "healthy", "service": "notification-service"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def get_user_email(user_id: int) -> str:
    """Get user email from user service"""
    try:
        response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
        if response.status_code == 200:
            user_data = response.json()
            return user_data.get("email", "unknown@example.com")
        else:
            return "unknown@example.com"
    except requests.RequestException:
        return "unknown@example.com"

def get_flight_details(flight_id: int) -> dict:
    """Get flight details from flight service"""
    try:
        response = requests.get(f"{FLIGHT_SERVICE_URL}/flights/{flight_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"flight_number": "Unknown", "origin": "Unknown", "destination": "Unknown"}
    except requests.RequestException:
        return {"flight_number": "Unknown", "origin": "Unknown", "destination": "Unknown"}

@app.post("/notifications", response_model=NotificationResponse)
async def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    """Create and send a notification"""
    # Get user email
    user_email = get_user_email(notification.user_id)
    
    # Get flight details
    flight_details = get_flight_details(notification.flight_id)
    
    # Create notification record
    db_notification = Notification(
        user_id=notification.user_id,
        booking_id=notification.booking_id,
        notification_type=NotificationType.BOOKING_CONFIRMATION,
        message=f"Booking {notification.booking_id} status: {notification.status}",
        sent_at=datetime.now()
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Send email notification
    try:
        email_content = {
            "to_email": user_email,
            "subject": f"Flight Booking {notification.status.title()}",
            "body": f"""
            Dear User,
            
            Your flight booking (ID: {notification.booking_id}) has been {notification.status}.
            
            Flight Details:
            - Flight Number: {flight_details.get('flight_number', 'Unknown')}
            - From: {flight_details.get('origin', 'Unknown')}
            - To: {flight_details.get('destination', 'Unknown')}
            - Amount: ${notification.amount}
            
            Thank you for choosing our service!
            """
        }
        
        send_email_notification(email_content)
        db_notification.status = "sent"
        NOTIFICATION_COUNT.labels(type="email", status="sent").inc()
        logger.info("Email notification sent", notification_id=db_notification.id, user_email=user_email)
        
    except Exception as e:
        db_notification.status = "failed"
        NOTIFICATION_COUNT.labels(type="email", status="failed").inc()
        logger.error("Failed to send email notification", notification_id=db_notification.id, error=str(e))
    
    db.commit()
    
    return NotificationResponse.from_orm(db_notification)

@app.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    user_id: int = None,
    booking_id: int = None,
    notification_type: NotificationType = None,
    db: Session = Depends(get_db)
):
    """Get notifications with optional filtering"""
    query = db.query(Notification)
    
    if user_id:
        query = query.filter(Notification.user_id == user_id)
    if booking_id:
        query = query.filter(Notification.booking_id == booking_id)
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    notifications = query.all()
    return [NotificationResponse.from_orm(notification) for notification in notifications]

@app.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int, db: Session = Depends(get_db)):
    """Get a specific notification by ID"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return NotificationResponse.from_orm(notification)

@app.post("/notifications/{notification_id}/resend")
async def resend_notification(notification_id: int, db: Session = Depends(get_db)):
    """Resend a notification"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Get user email
    user_email = get_user_email(notification.user_id)
    
    try:
        email_content = {
            "to_email": user_email,
            "subject": "Flight Booking Update (Resent)",
            "body": f"""
            Dear User,
            
            This is a resend of your notification:
            {notification.message}
            
            Thank you for choosing our service!
            """
        }
        
        send_email_notification(email_content)
        notification.status = "resent"
        notification.sent_at = datetime.now()
        
        db.commit()
        
        logger.info("Notification resent", notification_id=notification_id)
        return {"message": "Notification resent successfully"}
        
    except Exception as e:
        logger.error("Failed to resend notification", notification_id=notification_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend notification"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 