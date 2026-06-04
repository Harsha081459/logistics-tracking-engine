# Air-Travel Cargo Services Database Engine 🚀

A robust, production-ready logistics database engine and REST API serving a normalized MySQL schema. This system tracks complex supply chain networks with strict ACID transaction management and RBAC security.

## 🏗️ Architecture

- **Backend Framework**: FastAPI (Python)
- **Database**: MySQL 8.0 (Relational Database)
- **Deployment**: Docker & Docker Compose
- **Security**: JWT-based Authentication

## ✨ Key Features

1. **ACID-Compliant Transactions**: Handles multi-table inserts (Cargo, Booking, Tracking History) with `conn.commit()` and `conn.rollback()` to ensure zero data corruption during logistics updates.
2. **Referential Integrity**: Implements strict `ON DELETE CASCADE` foreign key constraints across a normalized 5-table schema.
3. **Complex JOINs**: Real-time aggregation of cargo status, customer data, and flight manifests via normalized query mapping.
4. **REST API**: Exposes core functionality via `/cargo` and `/shipments/{id}` endpoints.

## 🚀 Getting Started (Docker)

The entire application is containerized. You can spin up both the FastAPI web server and the MySQL database with a single command:

```bash
docker-compose up --build -d
```

Once running:
- **API Docs (Swagger UI)**: http://localhost:8000/docs
- **API Host**: http://localhost:8000

## 🔐 Authentication
The API utilizes a Bearer token dependency for endpoints. For local testing via Swagger UI, authorize using the mock JWT token:
`Bearer mock-jwt-admin-token-123`

## 💻 Legacy CLI Tool
The original terminal-based Python tool is preserved in `main.py` for legacy manual testing and direct database administration.
