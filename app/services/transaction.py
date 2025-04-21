#/app/services
from http.client import HTTPException

from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate

def get_transactions(db: Session, user_id: int) -> List[Transaction]:
    return db.query(Transaction).filter(Transaction.user_id == user_id).all()

def get_transaction(db: Session, transaction_id: int, user_id: int) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == user_id).first()

def create_transaction(db: Session, transaction_data: TransactionCreate, user_id: int) -> Transaction:
    transaction = Transaction(**transaction_data.dict(), user_id=user_id)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

def update_transaction(db: Session, transaction_id: int, transaction_data: TransactionUpdate, user_id: int) -> Transaction:
    transaction = get_transaction(db, transaction_id, user_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    for key, value in transaction_data.dict(exclude_unset=True).items():
        setattr(transaction, key, value)
    db.commit()
    db.refresh(transaction)
    return transaction

def delete_transaction(db: Session, transaction_id: int, user_id: int) -> None:
    transaction = get_transaction(db, transaction_id, user_id)
    if transaction:
        db.delete(transaction)
        db.commit()
