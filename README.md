# Order Management API

A FastAPI-based order management backend with authentication, role-based access control, product management, transactional order processing, PostgreSQL, Redis, Celery, Alembic, Docker, and automated tests.

## Features

- Customer registration and login
- JWT authentication
- Customer and admin roles
- Product creation and listing
- Transactional order creation
- Inventory validation and stock reduction
- Customer order history
- Admin order management
- Celery background confirmation tasks
- Redis message broker
- PostgreSQL database
- Alembic migrations
- Docker Compose
- Pytest automated tests
- GitHub Actions continuous integration

## Main technologies

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Redis
- Celery
- Docker
- Pytest

## Local setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1