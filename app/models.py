from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
    CheckConstraint,
)

from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="customer")

    orders = relationship("Order", back_populates="user")

    __table_args__ = (
        CheckConstraint("role IN ('customer', 'admin')", name="check_user_role"),
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    order_items = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        CheckConstraint("stock >= 0", name="check_product_stock_non_negative"),
        CheckConstraint("price >= 0", name="check_product_price_non_negative"),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(String(50), nullable=False, default="pending")
    total_amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="orders")

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')",
            name="check_order_status",
        ),
        CheckConstraint("total_amount >= 0", name="check_order_total_non_negative"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_order_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="check_order_item_price_non_negative"),
    )