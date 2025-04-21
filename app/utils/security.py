# app/utils/security.py
from jose import JWTError, jwt
from fastapi import HTTPException
from app.core.config import settings
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Хеширование пароля
def get_password_hash(password: str):
    return pwd_context.hash(password)

# Проверка пароля
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

"""Объяснение:
get_password_hash: принимает строку пароля и возвращает хешированное значение.

verify_password: проверяет, соответствует ли введённый пароль хешированному паролю."""


# Верификация токена
def verify_token(token: str):
    try:
        print(f"Received token: {token}")  # Для отладки
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise HTTPException(status_code=403, detail="Invalid token")

        print(f"Decoded payload: {payload}")  # Для отладки
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
