from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models import PaymentStatus

class PaymentBase(BaseModel):
    booking_id: int
    user_id: int
    amount: float

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    payment_id: str
    status: PaymentStatus
    processed_at: datetime
    refunded_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 