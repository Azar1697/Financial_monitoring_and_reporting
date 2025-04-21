#app/api
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionOut
from app.services.transaction import (
    get_transactions,
    get_transaction as get_transaction_by_id,
    create_transaction,
    update_transaction,
    delete_transaction,
)
from app.dependencies.oauth2 import oauth2_scheme
from app.utils.security import verify_token
from app.db.session import SessionLocal
from app.services.auth import get_user_by_email

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Получение всех транзакций текущего пользователя
@router.get("/", response_model=List[TransactionOut])
def read_transactions(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    email = payload.get("sub")
    user = get_user_by_email(db, email)
    return get_transactions(db, user_id=user.id)

# Получение конкретной транзакции по ID
@router.get("/{transaction_id}", response_model=TransactionOut)
def read_transaction(transaction_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    email = payload.get("sub")
    user = get_user_by_email(db, email)
    transaction = get_transaction_by_id(db, transaction_id, user.id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

# Создание новой транзакции
@router.post("/", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_new_transaction(transaction: TransactionCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    email = payload.get("sub")
    user = get_user_by_email(db, email)
    return create_transaction(db, transaction, user.id)

# Обновление транзакции
@router.put("/{transaction_id}", response_model=TransactionOut)
def update_existing_transaction(transaction_id: int, transaction: TransactionUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    email = payload.get("sub")
    user = get_user_by_email(db, email)
    return update_transaction(db, transaction_id, transaction, user.id)

# Удаление транзакции
@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_transaction(transaction_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    email = payload.get("sub")
    user = get_user_by_email(db, email)
    delete_transaction(db, transaction_id, user.id)
    return None
