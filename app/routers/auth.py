from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import User
from app.schemas import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.security import (
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
) -> User:
    """
    Register a new customer account.
    """

    normalized_email = user_data.email.lower().strip()

    existing_user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    new_user = User(
        email=normalized_email,
        hashed_password=hash_password(user_data.password),
        role="customer",
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to register user",
        )

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate a user and return a JWT access token.
    """

    normalized_email = login_data.email.lower().strip()

    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if not user or not verify_password(
        login_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )