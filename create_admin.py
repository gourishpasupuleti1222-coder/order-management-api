from app.database import SessionLocal
from app.models import User
from app.security import hash_password


ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


db = SessionLocal()

try:
    existing_admin = (
        db.query(User)
        .filter(User.email == ADMIN_EMAIL)
        .first()
    )

    if existing_admin:
        print("Admin already exists.")

    else:
        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role="admin",
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Admin created successfully.")
        print("Admin ID:", admin.id)
        print("Admin email:", admin.email)

finally:
    db.close()