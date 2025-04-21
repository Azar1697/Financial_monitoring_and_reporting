# app/services/auth.py

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.core.config import settings
from app.db.models.user import User
from app.db.session import SessionLocal
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, Token
from app.utils.security import verify_password, get_password_hash

# Настроим библиотеку для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция для создания пользователя
def create_user(db: Session, user: UserCreate):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise ValueError("User already exists")
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Функция для создания JWT токена
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Функция для авторизации (проверка пароля)
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

"""Объяснение:
create_user: функция для регистрации пользователя. Хеширует пароль и сохраняет нового пользователя в базе.

create_access_token: создаёт JWT токен, используя данные пользователя.

authenticate_user: проверяет, существует ли пользователь и соответствует ли пароль. Если все верно, возвращает пользователя."""

# Функция для получения пользователя по email
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()