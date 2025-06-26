from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FlightBase(BaseModel):
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    price: float
    total_seats: int
    available_seats: int

class FlightCreate(FlightBase):
    pass

class FlightUpdate(BaseModel):
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    price: Optional[float] = None
    total_seats: Optional[int] = None
    available_seats: Optional[int] = None
    is_active: Optional[bool] = None

class FlightResponse(FlightBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True 