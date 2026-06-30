from fastapi import FastAPI

from app import models
from app.database import  DATABASE_URL, engine
from app.routers import access, auth , orders, products





app = FastAPI(
    title="Order Management API",
    description="Phase 8: Authentication and RBAC",
    version="1.0.0",
)


app.include_router(auth.router)
app.include_router(access.router)
app.include_router(products.router)
app.include_router(orders.router)

@app.get("/", tags=["General"])
def root():
    return {
        "status": "running",
        "message": "Order Management API",
    }


@app.get("/health", tags=["Health"])
def application_health():
    return {
        "status": "healthy",
    }


@app.get("/db-check", tags=["Database"])
def db_check():
    return {
        "status": "database setup loaded",
        "database_url": DATABASE_URL,
        "engine": str(engine.url),
    }

