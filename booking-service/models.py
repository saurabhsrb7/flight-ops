from sqlalchemy import Column, Integer, String, DateTime, Float, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    flight_id = Column(Integer, nullable=False)
    seat_number = Column(Integer, nullable=False)
    booking_date = Column(DateTime, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    total_amount = Column(Float, nullable=False)
    payment_id = Column(String, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 