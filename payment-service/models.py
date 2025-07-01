from sqlalchemy import Column, Integer, String, DateTime, Float, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, unique=True, index=True, nullable=False)
    booking_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    processed_at = Column(DateTime, nullable=False)
    refunded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 