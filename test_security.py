from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

plain_password = "customer123"

hashed = hash_password(plain_password)

print("Plain password:", plain_password)
print("Hashed password:", hashed)

is_correct = verify_password("customer123", hashed)
is_wrong = verify_password("wrongpassword", hashed)

print("Correct password check:", is_correct)
print("Wrong password check:", is_wrong)

token = create_access_token(
    data={
        "sub": "1",
        "role": "customer",
    }
)

print("JWT token:", token)

payload = decode_access_token(token)

print("Decoded token payload:", payload)