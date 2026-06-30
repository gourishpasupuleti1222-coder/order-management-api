from decimal import Decimal
from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, Field


# -------------------------
# User Schemas
# -------------------------

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


# -------------------------
# Token Schemas
# -------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -------------------------
# Product Schemas
# -------------------------

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)


class ProductResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    stock: int

    class Config:
        from_attributes = True


# -------------------------
# Order Schemas
# -------------------------

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(pending|confirmed|shipped|delivered|cancelled)$"
    )

class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )
    stock: int | None = Field(
        default=None,
        ge=0,
    )