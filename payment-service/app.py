from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import uuid
import random

from database import get_db, engine
from models import Base, Payment
from schemas import PaymentCreate, PaymentResponse, PaymentStatus

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
PAYMENT_COUNT = Counter('payments_total', 'Total payments', ['status'])

app = FastAPI(title="Payment Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "healthy", "service": "payment-service"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def simulate_payment_processing(amount: float) -> PaymentStatus:
    """Simulate payment processing with random success/failure"""
    # Simulate 95% success rate
    if random.random() < 0.95:
        return PaymentStatus.SUCCESS
    else:
        return PaymentStatus.FAILED

@app.post("/payments", response_model=PaymentResponse)
async def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    """Process a payment"""
    # Generate payment ID
    payment_id = str(uuid.uuid4())
    
    # Simulate payment processing
    payment_status = simulate_payment_processing(payment.amount)
    
    # Create payment record
    db_payment = Payment(
        payment_id=payment_id,
        booking_id=payment.booking_id,
        user_id=payment.user_id,
        amount=payment.amount,
        status=payment_status,
        processed_at=datetime.now()
    )
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    PAYMENT_COUNT.labels(status=payment_status.value).inc()
    logger.info(
        "Payment processed", 
        payment_id=payment_id, 
        booking_id=payment.booking_id, 
        status=payment_status.value
    )
    
    return PaymentResponse.from_orm(db_payment)

@app.get("/payments", response_model=List[PaymentResponse])
async def get_payments(
    user_id: int = None,
    booking_id: int = None,
    status: PaymentStatus = None,
    db: Session = Depends(get_db)
):
    """Get payments with optional filtering"""
    query = db.query(Payment)
    
    if user_id:
        query = query.filter(Payment.user_id == user_id)
    if booking_id:
        query = query.filter(Payment.booking_id == booking_id)
    if status:
        query = query.filter(Payment.status == status)
    
    payments = query.all()
    return [PaymentResponse.from_orm(payment) for payment in payments]

@app.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: Session = Depends(get_db)):
    """Get a specific payment by ID"""
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return PaymentResponse.from_orm(payment)

@app.get("/payments/booking/{booking_id}", response_model=PaymentResponse)
async def get_payment_by_booking(booking_id: int, db: Session = Depends(get_db)):
    """Get payment by booking ID"""
    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found for this booking"
        )
    return PaymentResponse.from_orm(payment)

@app.post("/payments/{payment_id}/refund")
async def refund_payment(payment_id: str, db: Session = Depends(get_db)):
    """Refund a payment"""
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if payment.status != PaymentStatus.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment must be successful to be refunded"
        )
    
    # Simulate refund processing
    payment.status = PaymentStatus.REFUNDED
    payment.refunded_at = datetime.now()
    
    db.commit()
    
    logger.info("Payment refunded", payment_id=payment_id)
    return {"message": "Payment refunded successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 