from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.dependencies.oauth2 import oauth2_scheme
from app.schemas.user import UserCreate, Token, UserOut
from app.services.auth import create_user, authenticate_user, create_access_token, get_user_by_email
from app.utils.security import verify_token
from fastapi import status



router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Роут для регистрации
@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Роут для логина
@router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Роут для получения данных пользователя
@router.get("/profile", response_model=UserOut)
def get_profile(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = verify_token(token)
        email = payload.get("sub")
        user = get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user  # <= должно возвращать объект с полем `email`
    except HTTPException:
        raise HTTPException(status_code=403, detail="Invalid token or expired token")
"""
@router.post("/", response_model=Token)
def main(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = verify_token(token)
        email = payload.get("sub")
        user = get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise HTTPException(status_code=403, detail="Invalid token or expired token")
"""