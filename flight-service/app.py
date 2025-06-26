from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import os
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from database import get_db, Base
from schemas import FlightCreate, FlightResponse, FlightUpdate

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

def create_app(engine=None, sessionmaker=None):
    """Factory function to create FastAPI app with configurable database"""
    app = FastAPI(title="Flight Service", version="1.0.0")
    
    # Override database dependencies if provided
    if engine and sessionmaker:
        from database import set_engine_and_session
        set_engine_and_session(engine, sessionmaker)
    
    # Import models after engine is set to ensure they use the correct database
    from models import Flight
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    
    # API endpoints
    @app.post("/flights", response_model=FlightResponse)
    def create_flight(flight: FlightCreate, db: Session = Depends(get_db)):
        """Create a new flight"""
        db_flight = Flight(
            flight_number=flight.flight_number,
            airline=flight.airline,
            origin=flight.origin,
            destination=flight.destination,
            departure_time=flight.departure_time,
            arrival_time=flight.arrival_time,
            total_seats=flight.total_seats,
            available_seats=flight.available_seats,
            price=flight.price
        )
        db.add(db_flight)
        db.commit()
        db.refresh(db_flight)
        return db_flight
    
    @app.get("/flights", response_model=List[FlightResponse])
    def get_flights(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
        """Get all flights"""
        flights = db.query(Flight).offset(skip).limit(limit).all()
        return flights
    
    @app.get("/flights/search", response_model=List[FlightResponse])
    def search_flights(
        origin: str = Query(..., description="Origin airport code"),
        destination: str = Query(..., description="Destination airport code"),
        departure_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
        db: Session = Depends(get_db)
    ):
        """Search flights by origin, destination, and date"""
        try:
            date_obj = datetime.strptime(departure_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        flights = db.query(Flight).filter(
            Flight.origin == origin,
            Flight.destination == destination,
            Flight.departure_time >= date_obj,
            Flight.departure_time < date_obj + timedelta(days=1)
        ).all()
        
        return flights
    
    @app.get("/flights/{flight_id}", response_model=FlightResponse)
    def get_flight(flight_id: int, db: Session = Depends(get_db)):
        """Get a specific flight by ID"""
        flight = db.query(Flight).filter(Flight.id == flight_id).first()
        if not flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flight not found"
            )
        return flight
    
    @app.put("/flights/{flight_id}", response_model=FlightResponse)
    def update_flight(flight_id: int, flight_update: FlightUpdate, db: Session = Depends(get_db)):
        """Update a flight"""
        db_flight = db.query(Flight).filter(Flight.id == flight_id).first()
        if not db_flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flight not found"
            )
        
        for field, value in flight_update.dict(exclude_unset=True).items():
            setattr(db_flight, field, value)
        
        db.commit()
        db.refresh(db_flight)
        return db_flight
    
    @app.delete("/flights/{flight_id}")
    def delete_flight(flight_id: int, db: Session = Depends(get_db)):
        """Delete a flight"""
        db_flight = db.query(Flight).filter(Flight.id == flight_id).first()
        if not db_flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flight not found"
            )
        
        db.delete(db_flight)
        db.commit()
        return {"message": "Flight deleted successfully"}
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy", "service": "flight-service"}
    
    return app

app = create_app()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

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

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 