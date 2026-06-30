from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User
from app.security import decode_access_token


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Create one database session for each API request.

    The session is closed automatically after the request finishes.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Read the Bearer token, decode it, and return the matching user.
    """

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_error

    token = credentials.credentials

    try:
        payload = decode_access_token(token)

        user_id_value = payload.get("sub")

        if user_id_value is None:
            raise credentials_error

        user_id = int(user_id_value)

    except (ValueError, TypeError):
        raise credentials_error

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise credentials_error

    return user


def require_customer(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Allow only users whose database role is customer.
    """

    if current_user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer access required",
        )

    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Allow only users whose database role is admin.
    """

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user