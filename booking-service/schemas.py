from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models import BookingStatus

class BookingBase(BaseModel):
    user_id: int
    flight_id: int
    seat_number: int

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: int
    booking_date: datetime
    status: BookingStatus
    total_amount: float
    payment_id: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 