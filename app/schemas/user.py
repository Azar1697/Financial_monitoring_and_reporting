# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from typing import Optional

# Схема для регистрации пользователя
class UserCreate(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True

# Схема для вывода данных о пользователе
class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        orm_mode = True

# Схема для JWT токена
class Token(BaseModel):
    access_token: str
    token_type: str

# Схема для данных из токена
class TokenData(BaseModel):
    email: str
    id: int
"""
Объяснение:
UserCreate: используется для регистрации пользователя. Получает email и password.

UserOut: используется для вывода информации о пользователе (например, после авторизации).

Token: схема для возвращаемого токена.

TokenData: данные, которые мы получаем из токена для проверки авторизованного пользователя
"""

