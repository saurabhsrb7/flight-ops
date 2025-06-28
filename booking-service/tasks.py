import requests
import structlog
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Booking, BookingStatus

logger = structlog.get_logger()

PAYMENT_SERVICE_URL = "http://localhost:8003"
NOTIFICATION_SERVICE_URL = "http://localhost:8004"

def process_payment_task(booking_id: int):
    """Background task to process payment"""
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logger.error("Booking not found for payment processing", booking_id=booking_id)
            return
        
        # Simulate payment processing
        payment_data = {
            "booking_id": booking_id,
            "amount": booking.total_amount,
            "user_id": booking.user_id
        }
        
        try:
            response = requests.post(f"{PAYMENT_SERVICE_URL}/payments", json=payment_data)
            if response.status_code == 200:
                payment_result = response.json()
                booking.payment_id = payment_result.get("payment_id")
                booking.status = BookingStatus.CONFIRMED
                logger.info("Payment processed successfully", booking_id=booking_id, payment_id=booking.payment_id)
            else:
                booking.status = BookingStatus.FAILED
                logger.error("Payment processing failed", booking_id=booking_id, status_code=response.status_code)
        except requests.RequestException as e:
            booking.status = BookingStatus.FAILED
            logger.error("Payment service unavailable", booking_id=booking_id, error=str(e))
        
        db.commit()
        
    except Exception as e:
        logger.error("Error in payment processing", booking_id=booking_id, error=str(e))
    finally:
        db.close()

def send_notification_task(booking_id: int):
    """Background task to send notification"""
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logger.error("Booking not found for notification", booking_id=booking_id)
            return
        
        # Prepare notification data
        notification_data = {
            "booking_id": booking_id,
            "user_id": booking.user_id,
            "flight_id": booking.flight_id,
            "status": booking.status.value,
            "amount": booking.total_amount
        }
        
        try:
            response = requests.post(f"{NOTIFICATION_SERVICE_URL}/notifications", json=notification_data)
            if response.status_code == 200:
                logger.info("Notification sent successfully", booking_id=booking_id)
            else:
                logger.error("Failed to send notification", booking_id=booking_id, status_code=response.status_code)
        except requests.RequestException as e:
            logger.error("Notification service unavailable", booking_id=booking_id, error=str(e))
        
    except Exception as e:
        logger.error("Error in notification sending", booking_id=booking_id, error=str(e))
    finally:
        db.close() 