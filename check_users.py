from app.database import SessionLocal
from app.models import User


db = SessionLocal()

try:
    users = db.query(User).all()

    print("Users in database:")

    for user in users:
        print(
            f"id={user.id}, "
            f"email={user.email}, "
            f"role={user.role}, "
            f"password_is_hashed={user.hashed_password != 'customer123'}"
        )

finally:
    db.close()