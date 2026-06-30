from fastapi import APIRouter, Depends

from app.dependencies import (
    get_current_user,
    require_admin,
    require_customer,
)
from app.models import User
from app.schemas import UserResponse


router = APIRouter(
    tags=["Access Control"],
)


@router.get(
    "/users/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Any authenticated user can view their own account information.
    """
    return current_user


@router.get("/customer/check")
def customer_access_check(
    current_user: User = Depends(require_customer),
):
    """
    Customer-only test endpoint.
    """
    return {
        "message": "Customer access granted",
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.get("/admin/check")
def admin_access_check(
    current_user: User = Depends(require_admin),
):
    """
    Admin-only test endpoint.
    """
    return {
        "message": "Admin access granted",
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
    }