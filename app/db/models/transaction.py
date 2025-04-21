from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.db.base import Base


class PersonType(str, PyEnum):
    individual = "Физическое лицо"
    legal = "Юридическое лицо"


class TransactionType(str, PyEnum):
    income = "Поступление"
    expense = "Списание"


class TransactionStatus(str, PyEnum):
    new = "Новая"
    confirmed = "Подтвержденная"
    processing = "В обработке"
    canceled = "Отменена"
    completed = "Платеж выполнен"
    deleted = "Платеж удален"
    refund = "Возврат"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    person_type = Column(Enum(PersonType), nullable=False)
    date_time = Column(DateTime, default=datetime.utcnow)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    comment = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False)
    sender_bank = Column(String, nullable=True)
    sender_account = Column(String, nullable=True)
    recipient_bank = Column(String, nullable=True)
    recipient_inn = Column(String, nullable=False)
    recipient_account = Column(String, nullable=True)
    category = Column(String, nullable=True)
    recipient_phone = Column(String, nullable=True)

    # 🔗 Связь с пользователем
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="transactions")
