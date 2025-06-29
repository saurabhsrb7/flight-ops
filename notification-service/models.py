from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.sql import func
from database import Base
import enum

class NotificationType(str, enum.Enum):
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_CANCELLATION = "booking_cancellation"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    FLIGHT_UPDATE = "flight_update"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    booking_id = Column(Integer, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, sent, failed, resent
    sent_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 