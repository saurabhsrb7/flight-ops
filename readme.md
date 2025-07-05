# ✈️ Real-Time Flight Ticket Booking System (DevOps Project)

A modern, microservices-based flight ticket booking system built with FastAPI, PostgreSQL, Redis, and Docker. This project demonstrates scalable architecture, real-time seat locking, payment processing, and notification services.

## 🏗️ Architecture

The system is built using a microservices architecture with the following components:

### Core Services

- **User Service** (`:8000`) - User authentication, registration, and profile management
- **Flight Service** (`:8001`) - Flight information, availability, and seat management
- **Booking Service** (`:8002`) - Ticket booking with real-time seat locking
- **Payment Service** (`:8003`) - Payment processing and transaction management
- **Notification Service** (`:8004`) - Email notifications and booking confirmations

### Infrastructure

- **PostgreSQL** - Separate databases for each service (ports 5432-5436)
- **Redis** (`:6379`) - Caching and seat locking mechanism
- **Docker Compose** - Container orchestration and service management

## 🚀 Features

- 🔐 **JWT Authentication** - Secure user authentication with token-based sessions
- 🪑 **Real-time Seat Locking** - Redis-based concurrency control for seat reservations
- 💳 **Payment Processing** - Background payment processing with status tracking
- 📧 **Email Notifications** - Automated booking confirmations and updates
- 📊 **Monitoring** - Prometheus metrics and structured logging
- 🧪 **Comprehensive Testing** - Unit and integration tests for all services
- 🔄 **Background Tasks** - Asynchronous processing for payments and notifications

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL 15
- **Caching**: Redis 7
- **Authentication**: JWT with bcrypt password hashing
- **Monitoring**: Prometheus metrics, Structlog
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest with test databases

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd flight-ops
```

### 2. Start All Services

```bash
docker-compose up -d
```

This will start all services and their dependencies:
- 5 PostgreSQL databases
- Redis cache
- 5 microservices

### 3. Initialize Databases

The services will automatically create their database tables on startup.

### 4. Access Services

- **User Service**: http://localhost:8000
- **Flight Service**: http://localhost:8001
- **Booking Service**: http://localhost:8002
- **Payment Service**: http://localhost:8003
- **Notification Service**: http://localhost:8004

## 📚 API Documentation

### User Service (`:8000`)

#### Authentication Endpoints

```bash
# Register a new user
POST /register
{
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "password": "securepassword"
}

# Login and get access token
POST /token
Content-Type: application/x-form-urlencoded
username=johndoe&password=securepassword

# Get current user profile
GET /users/me
Authorization: Bearer <access_token>
```

#### Health & Monitoring

```bash
# Health check
GET /health

# Prometheus metrics
GET /metrics
```

### Flight Service (`:8001`)

```bash
# Get all flights
GET /flights

# Get specific flight
GET /flights/{flight_id}

# Create new flight
POST /flights
{
  "flight_number": "FL123",
  "origin": "JFK",
  "destination": "LAX",
  "departure_time": "2024-01-15T10:00:00",
  "arrival_time": "2024-01-15T13:00:00",
  "total_seats": 150,
  "price": 299.99
}
```

### Booking Service (`:8002`)

```bash
# Create a booking
POST /bookings
{
  "user_id": 1,
  "flight_id": 1,
  "seat_number": "12A"
}

# Get user bookings
GET /bookings?user_id=1

# Get booking status
GET /bookings/{booking_id}/status

# Cancel booking
PUT /bookings/{booking_id}/cancel
```

### Payment Service (`:8003`)

```bash
# Process payment
POST /payments
{
  "booking_id": 1,
  "amount": 299.99,
  "payment_method": "credit_card",
  "card_number": "4111111111111111"
}

# Get payment status
GET /payments/{payment_id}
```

### Notification Service (`:8004`)

```bash
# Send notification
POST /notifications
{
  "user_id": 1,
  "type": "booking_confirmation",
  "message": "Your booking has been confirmed"
}

# Get user notifications
GET /notifications?user_id=1
```

## 🧪 Testing

### Run Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests for a specific service
cd user-service
python -m pytest tests/

# Run all tests
find . -name "test_*.py" -exec python -m pytest {} \;
```

### Test Coverage

Each service includes comprehensive tests:
- Unit tests for models and schemas
- Integration tests for API endpoints
- Database transaction tests
- Authentication and authorization tests

## 📊 Monitoring & Observability

### Metrics

All services expose Prometheus metrics at `/metrics`:
- HTTP request counts and latencies
- Business metrics (bookings, payments, etc.)
- Database connection metrics

### Logging

Structured logging with JSON format:
- Request/response logging
- Error tracking
- Business event logging

### Health Checks

Each service provides health check endpoints:
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
# ... etc
```

## 🔧 Configuration

### Environment Variables

Key configuration options:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/service_name

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key-here

# Email (Notification Service)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Service Dependencies

```
User Service ← Booking Service
Flight Service ← Booking Service
Booking Service ← Payment Service
Booking Service ← Notification Service
```

## 🐳 Docker

### Build Images

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build user-service
```

### Development

```bash
# Start in development mode with logs
docker-compose up

# Start specific service
docker-compose up user-service

# View logs
docker-compose logs -f user-service
```

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure session management
- **CORS**: Configurable cross-origin requests
- **Input Validation**: Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM

## 📈 Scalability

- **Microservices**: Independent scaling of services
- **Database Separation**: Isolated data per service
- **Caching**: Redis for frequently accessed data
- **Background Tasks**: Asynchronous processing
- **Load Balancing**: Ready for horizontal scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at service endpoints
2. Review the test files for usage examples
3. Check service logs: `docker-compose logs <service-name>`

---

**Happy Flying! ✈️**
