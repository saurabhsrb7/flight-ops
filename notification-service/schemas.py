from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models import NotificationType

class NotificationBase(BaseModel):
    user_id: int
    booking_id: int
    flight_id: int
    status: str
    amount: float

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    booking_id: int
    notification_type: NotificationType
    message: str
    status: str
    sent_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True 