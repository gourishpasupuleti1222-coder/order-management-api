from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.dependencies import (
    get_current_user,
    get_db,
    require_admin,
    require_customer,
)
from app.models import Order, OrderItem, Product, User
from app.schemas import (OrderCreate, OrderResponse, OrderStatusUpdate)
from app.tasks import send_order_confirmation_email

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
) -> Order:
    """
    Create an order for the authenticated customer.

    All product checks, stock reductions, the order, and order items
    are saved as one database transaction.
    """

    # Prevent the same product from appearing more than once.
    product_ids = [
        item.product_id
        for item in order_data.items
    ]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Each product can appear only once in an order. "
                "Increase its quantity instead."
            ),
        )

    try:
        prepared_items: list[dict] = []
        total_amount = Decimal("0.00")

        # Sort IDs to lock rows consistently.
        sorted_items = sorted(
            order_data.items,
            key=lambda item: item.product_id,
        )

        for requested_item in sorted_items:
            product_statement = (
                select(Product)
                .where(Product.id == requested_item.product_id)
                .with_for_update()
            )

            product = db.execute(
                product_statement
            ).scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Product {requested_item.product_id} "
                        "was not found"
                    ),
                )

            if product.stock < requested_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Insufficient stock for {product.name}. "
                        f"Available: {product.stock}, "
                        f"requested: {requested_item.quantity}"
                    ),
                )

            line_total = (
                product.price * requested_item.quantity
            )

            total_amount += line_total

            prepared_items.append(
                {
                    "product": product,
                    "quantity": requested_item.quantity,
                    "unit_price": product.price,
                }
            )

        order = Order(
            user_id=current_user.id,
            status="pending",
            total_amount=total_amount,
        )

        db.add(order)

        # Generate order.id without committing.
        db.flush()

        for prepared_item in prepared_items:
            product = prepared_item["product"]
            quantity = prepared_item["quantity"]
            unit_price = prepared_item["unit_price"]

            product.stock -= quantity

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
            )

            db.add(order_item)

        # Save the order, order items, and inventory updates together.
        db.commit()

        created_order_statement = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order.id)
        )

        created_order = db.execute(
            created_order_statement
        ).scalar_one()

        try:
           send_order_confirmation_email.delay(
               customer_email=current_user.email,
               order_id=created_order.id,
               total_amount=str(created_order.total_amount),
    )

        except Exception as task_error:
           print(
                 "WARNING: Order was created, but the confirmation "
                 f"email task could not be queued: {task_error}"
    )

        return created_order

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error prevented order creation",
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create order",
        )
    
@router.get(
    "/my",
    response_model=list[OrderResponse],
)
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
) -> list[Order]:
    """
    Return all orders belonging to the authenticated customer.
    """

    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )

    orders = db.execute(
        statement
    ).scalars().all()

    return list(orders)

@router.get(
    "",
    response_model=list[OrderResponse],
)
def get_all_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[Order]:
    """
    Return all orders.

    Admin only.
    """

    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )

    orders = db.execute(
        statement
    ).scalars().all()

    return list(orders)

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    """
    Return one order.

    Customers can access only their own orders.
    Admins can access any order.
    """

    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )

    order = db.execute(
        statement
    ).scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if (
        current_user.role == "customer"
        and order.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="order not found",
        )

    return order

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Order:
    """
    Update one order's status.

    Admin only.
    """

    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )

    order = db.execute(
        statement
    ).scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    allowed_transitions = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"shipped", "cancelled"},
        "shipped": {"delivered"},
        "delivered": set(),
        "cancelled": set(),
    }

    current_status = order.status
    requested_status = status_data.status

    if requested_status == current_status:
        return order

    allowed_next_statuses = allowed_transitions.get(
        current_status,
        set(),
    )

    if requested_status not in allowed_next_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Order status cannot change from "
                f"'{current_status}' to '{requested_status}'"
            ),
        )

    try:
        order.status = requested_status

        db.commit()
        db.refresh(order)

        refreshed_statement = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order.id)
        )

        updated_order = db.execute(
            refreshed_statement
        ).scalar_one()

        return updated_order

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error prevented the status update",
        )