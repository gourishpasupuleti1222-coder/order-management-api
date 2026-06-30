from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Product, User
from app.security import hash_password


CUSTOMER_EMAIL = "customer@example.com"
CUSTOMER_PASSWORD = "customer123"

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


def register_customer(
    client: TestClient,
    email: str = CUSTOMER_EMAIL,
    password: str = CUSTOMER_PASSWORD,
):
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )


def login_user(
    client: TestClient,
    email: str,
    password: str,
) -> str:
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"

    return response_data["access_token"]


def authorization_header(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_admin(
    db: Session,
) -> User:
    admin = User(
        email=ADMIN_EMAIL,
        hashed_password=hash_password(ADMIN_PASSWORD),
        role="admin",
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin


def create_customer_and_get_token(
    client: TestClient,
) -> str:
    registration_response = register_customer(client)

    assert registration_response.status_code == 201

    return login_user(
        client,
        CUSTOMER_EMAIL,
        CUSTOMER_PASSWORD,
    )


def create_admin_and_get_token(
    client: TestClient,
    db: Session,
) -> str:
    create_admin(db)

    return login_user(
        client,
        ADMIN_EMAIL,
        ADMIN_PASSWORD,
    )


def test_health_check(
    client: TestClient,
):
    response = client.get("/")

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["status"] == "running"


def test_customer_registration(
    client: TestClient,
):
    response = register_customer(client)

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["email"] == CUSTOMER_EMAIL
    assert response_data["role"] == "customer"
    assert "id" in response_data
    assert "password" not in response_data
    assert "hashed_password" not in response_data


def test_duplicate_customer_registration_is_rejected(
    client: TestClient,
):
    first_response = register_customer(client)
    second_response = register_customer(client)

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": "An account with this email already exists"
    }


def test_customer_login_returns_token(
    client: TestClient,
):
    register_customer(client)

    response = client.post(
        "/auth/login",
        json={
            "email": CUSTOMER_EMAIL,
            "password": CUSTOMER_PASSWORD,
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["access_token"]
    assert response_data["token_type"] == "bearer"


def test_wrong_password_is_rejected(
    client: TestClient,
):
    register_customer(client)

    response = client.post(
        "/auth/login",
        json={
            "email": CUSTOMER_EMAIL,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid email or password"
    }


def test_admin_can_create_product(
    client: TestClient,
    db: Session,
):
    admin_token = create_admin_and_get_token(client, db)

    response = client.post(
        "/products",
        headers=authorization_header(admin_token),
        json={
            "name": "Test Laptop",
            "price": 999.99,
            "stock": 10,
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["name"] == "Test Laptop"
    assert response_data["stock"] == 10
    assert str(response_data["price"]) == "999.99"


def test_customer_cannot_create_product(
    client: TestClient,
):
    customer_token = create_customer_and_get_token(client)

    response = client.post(
        "/products",
        headers=authorization_header(customer_token),
        json={
            "name": "Forbidden Product",
            "price": 99.99,
            "stock": 5,
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Admin access required"
    }


def test_customer_can_create_order_and_stock_decreases(
    client: TestClient,
    db: Session,
):
    customer_token = create_customer_and_get_token(client)

    product = Product(
        name="Test Phone",
        price=500.00,
        stock=10,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    with patch(
        "app.routers.orders."
        "send_order_confirmation_email.delay"
    ) as mocked_email_task:
        response = client.post(
            "/orders",
            headers=authorization_header(customer_token),
            json={
                "items": [
                    {
                        "product_id": product.id,
                        "quantity": 2,
                    }
                ]
            },
        )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["status"] == "pending"
    assert str(response_data["total_amount"]) == "1000.00"
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["quantity"] == 2

    db.refresh(product)

    assert product.stock == 8

    mocked_email_task.assert_called_once()


def test_order_with_insufficient_stock_is_rejected(
    client: TestClient,
    db: Session,
):
    customer_token = create_customer_and_get_token(client)

    product = Product(
        name="Low Stock Product",
        price=25.00,
        stock=1,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    with patch(
        "app.routers.orders."
        "send_order_confirmation_email.delay"
    ) as mocked_email_task:
        response = client.post(
            "/orders",
            headers=authorization_header(customer_token),
            json={
                "items": [
                    {
                        "product_id": product.id,
                        "quantity": 5,
                    }
                ]
            },
        )

    assert response.status_code == 409

    db.refresh(product)

    assert product.stock == 1
    mocked_email_task.assert_not_called()


def test_customer_can_view_own_orders(
    client: TestClient,
    db: Session,
):
    customer_token = create_customer_and_get_token(client)

    product = Product(
        name="Order History Product",
        price=100.00,
        stock=10,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    with patch(
        "app.routers.orders."
        "send_order_confirmation_email.delay"
    ):
        create_response = client.post(
            "/orders",
            headers=authorization_header(customer_token),
            json={
                "items": [
                    {
                        "product_id": product.id,
                        "quantity": 1,
                    }
                ]
            },
        )

    assert create_response.status_code == 201

    orders_response = client.get(
        "/orders/my",
        headers=authorization_header(customer_token),
    )

    assert orders_response.status_code == 200

    orders = orders_response.json()

    assert len(orders) == 1
    assert orders[0]["id"] == create_response.json()["id"]


def test_admin_can_view_all_orders(
    client: TestClient,
    db: Session,
):
    customer_token = create_customer_and_get_token(client)

    product = Product(
        name="Admin View Product",
        price=75.00,
        stock=10,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    with patch(
        "app.routers.orders."
        "send_order_confirmation_email.delay"
    ):
        order_response = client.post(
            "/orders",
            headers=authorization_header(customer_token),
            json={
                "items": [
                    {
                        "product_id": product.id,
                        "quantity": 1,
                    }
                ]
            },
        )

    assert order_response.status_code == 201

    admin_token = create_admin_and_get_token(client, db)

    response = client.get(
        "/orders",
        headers=authorization_header(admin_token),
    )

    assert response.status_code == 200

    orders = response.json()

    assert len(orders) == 1


def test_admin_can_update_order_status(
    client: TestClient,
    db: Session,
):
    customer_token = create_customer_and_get_token(client)

    product = Product(
        name="Status Product",
        price=150.00,
        stock=10,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    with patch(
        "app.routers.orders."
        "send_order_confirmation_email.delay"
    ):
        order_response = client.post(
            "/orders",
            headers=authorization_header(customer_token),
            json={
                "items": [
                    {
                        "product_id": product.id,
                        "quantity": 1,
                    }
                ]
            },
        )

    assert order_response.status_code == 201

    order_id = order_response.json()["id"]

    admin_token = create_admin_and_get_token(client, db)

    update_response = client.patch(
        f"/orders/{order_id}/status",
        headers=authorization_header(admin_token),
        json={
            "status": "confirmed",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "confirmed"