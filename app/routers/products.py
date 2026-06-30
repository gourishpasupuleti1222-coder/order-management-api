from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_admin
from app.models import Product, User
from app.schemas import ProductCreate, ProductResponse


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Product:
    """
    Create a new product.

    Only admin users can access this endpoint.
    """

    normalized_name = product_data.name.strip()

    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Product name cannot be empty",
        )

    existing_product = (
        db.query(Product)
        .filter(Product.name == normalized_name)
        .first()
    )

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this name already exists",
        )

    new_product = Product(
        name=normalized_name,
        price=product_data.price,
        stock=product_data.stock,
    )

    try:
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create product",
        )

    return new_product


@router.get(
    "",
    response_model=list[ProductResponse],
)
def get_products(
    db: Session = Depends(get_db),
) -> list[Product]:
    """
    Return all products.

    This endpoint is public.
    """

    products = (
        db.query(Product)
        .order_by(Product.id.asc())
        .all()
    )

    return products


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
) -> Product:
    """
    Return one product by its ID.

    This endpoint is public.
    """

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product