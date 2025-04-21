from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class PersonType(str, Enum):
    individual = "Физическое лицо"
    legal = "Юридическое лицо"


class TransactionType(str, Enum):
    income = "Поступление"
    expense = "Списание"


class TransactionStatus(str, Enum):
    new = "Новая"
    confirmed = "Подтвержденная"
    processing = "В обработке"
    canceled = "Отменена"
    completed = "Платеж выполнен"
    deleted = "Платеж удален"
    refund = "Возврат"


class TransactionBase(BaseModel):
    person_type: PersonType
    date_time: datetime
    transaction_type: TransactionType
    comment: Optional[str]
    amount: float = Field(..., gt=0, le=999999.99999)
    status: TransactionStatus
    sender_bank: Optional[str]
    sender_account: Optional[str]
    recipient_bank: Optional[str]
    recipient_inn: str = Field(..., pattern=r"^\d{10,11}$")
    recipient_account: Optional[str]
    category: Optional[str]
    recipient_phone: Optional[str] = Field(None, pattern=r"^(\+7|8)\d{10}$")


class TransactionCreate(TransactionBase):
    pass


class TransactionOut(TransactionBase):
    id: int

    class Config:
        orm_mode = True


class TransactionUpdate(BaseModel):
    person_type: Optional[PersonType]
    date_time: Optional[datetime]
    comment: Optional[str]
    amount: Optional[float]
    status: Optional[TransactionStatus]
    sender_bank: Optional[str]
    sender_account: Optional[str]
    recipient_bank: Optional[str]
    recipient_inn: Optional[str] = Field(None, pattern=r"^\d{10,11}$")
    recipient_account: Optional[str]
    category: Optional[str]
    recipient_phone: Optional[str] = Field(None, pattern=r"^(\+7|8)\d{10}$")
