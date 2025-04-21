from datetime import datetime, date
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.dependencies.oauth2 import oauth2_scheme
from app.db.session import SessionLocal
from app.db.models.transaction import Transaction as TransactionModel
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionOut,
    TransactionType,
    TransactionStatus,
)
from app.services.transaction import (
    get_transaction as get_transaction_by_id,
    create_transaction,
    update_transaction,
    delete_transaction,
)
from app.services.auth import get_user_by_email
from app.utils.security import verify_token

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "/",
    response_model=List[TransactionOut],
    summary="Список транзакций с фильтрацией",
)
def read_transactions(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    start_date:      Optional[date]             = Query(None, description="Дата от (YYYY-MM-DD)"),
    end_date:        Optional[date]             = Query(None, description="Дата до (YYYY-MM-DD)"),
    status_:         Optional[TransactionStatus] = Query(None, alias="status",           description="Статус транзакции"),
    transaction_type:Optional[TransactionType]   = Query(None, alias="type",             description="Тип транзакции"),
    min_amount:      Optional[float]            = Query(None, ge=0,                      description="Минимальная сумма"),
    max_amount:      Optional[float]            = Query(None, ge=0,                      description="Максимальная сумма"),
    category:        Optional[str]              = Query(None,                           description="Категория"),
    sender_bank:     Optional[str]              = Query(None,                           description="Банк отправителя"),
    recipient_bank:  Optional[str]              = Query(None,                           description="Банк получателя"),
    recipient_inn:   Optional[str]              = Query(None,                           description="ИНН получателя"),
):
    """
    Получить транзакции текущего пользователя с опциональной фильтрацией по:
    дате, сумме, статусу, типу, категории, банкам и ИНН.
    """
    payload = verify_token(token)
    user = get_user_by_email(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    q = db.query(TransactionModel).filter(TransactionModel.user_id == user.id)

    if start_date:
        q = q.filter(TransactionModel.date_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        q = q.filter(TransactionModel.date_time <= datetime.combine(end_date,   datetime.max.time()))
    if status_:
        q = q.filter(TransactionModel.status == status_)
    if transaction_type:
        q = q.filter(TransactionModel.transaction_type == transaction_type)
    if min_amount is not None:
        q = q.filter(TransactionModel.amount >= min_amount)
    if max_amount is not None:
        q = q.filter(TransactionModel.amount <= max_amount)
    if category:
        q = q.filter(TransactionModel.category == category)
    if sender_bank:
        q = q.filter(TransactionModel.sender_bank == sender_bank)
    if recipient_bank:
        q = q.filter(TransactionModel.recipient_bank == recipient_bank)
    if recipient_inn:
        q = q.filter(TransactionModel.recipient_inn == recipient_inn)

    return q.all()


@router.get(
    "/stats",
    summary="Статистика и данные для дашбордов",
    response_model=Dict[str, Any],
)
def get_statistics(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    start_date:     Optional[date]             = Query(None, description="Дата от"),
    end_date:       Optional[date]             = Query(None, description="Дата до"),
    status_:        Optional[TransactionStatus] = Query(None, alias="status", description="Статус"),
    transaction_type: Optional[TransactionType] = Query(None, alias="type",   description="Тип"),
    min_amount:     Optional[float]            = Query(None, ge=0, description="Мин. сумма"),
    max_amount:     Optional[float]            = Query(None, ge=0, description="Макс. сумма"),
    category:       Optional[str]              = Query(None, description="Категория"),
    sender_bank:    Optional[str]              = Query(None, description="Банк отправителя"),
    recipient_bank: Optional[str]              = Query(None, description="Банк получателя"),
    recipient_inn:  Optional[str]              = Query(None, description="ИНН"),
):
    """
    Возвращает агрегированные данные для дашборда:
     1) Ежемесячное кол-во
     2) Кол-во по типам (доход/расход)
     3) Суммы доходов и расходов
     4) Кол-во по статусам
     5) Кол-во по банкам отправителя
     6) Кол-во по банкам получателя
    С учётом тех же фильтров, что и основной список.
    """
    payload = verify_token(token)
    user = get_user_by_email(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Собираем все фильтры
    base_filters = [TransactionModel.user_id == user.id]
    if start_date:
        base_filters.append(TransactionModel.date_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        base_filters.append(TransactionModel.date_time <= datetime.combine(end_date,   datetime.max.time()))
    if status_:
        base_filters.append(TransactionModel.status == status_)
    if transaction_type:
        base_filters.append(TransactionModel.transaction_type == transaction_type)
    if min_amount is not None:
        base_filters.append(TransactionModel.amount >= min_amount)
    if max_amount is not None:
        base_filters.append(TransactionModel.amount <= max_amount)
    if category:
        base_filters.append(TransactionModel.category == category)
    if sender_bank:
        base_filters.append(TransactionModel.sender_bank == sender_bank)
    if recipient_bank:
        base_filters.append(TransactionModel.recipient_bank == recipient_bank)
    if recipient_inn:
        base_filters.append(TransactionModel.recipient_inn == recipient_inn)

    # 1) Ежемесячное количество транзакций
    monthly = (
        db.query(
            func.date_trunc('month', TransactionModel.date_time).label('period'),
            func.count().label('count')
        )
        .filter(*base_filters)
        .group_by(func.date_trunc('month', TransactionModel.date_time))
        .order_by(func.date_trunc('month', TransactionModel.date_time))
        .all()
    )

    # 2) Кол-во по типам
    by_type = (
        db.query(
            TransactionModel.transaction_type,
            func.count().label('count')
        )
        .filter(*base_filters)
        .group_by(TransactionModel.transaction_type)
        .all()
    )

    # 3) Суммы доходов и расходов (case() теперь принимает кортежи как позиционные аргументы)
    sums = (
        db.query(
            func.sum(
                case(
                    (TransactionModel.transaction_type == TransactionType.income, TransactionModel.amount),
                    else_=0
                )
            ).label('income'),
            func.sum(
                case(
                    (TransactionModel.transaction_type == TransactionType.expense, TransactionModel.amount),
                    else_=0
                )
            ).label('expense')
        )
        .filter(*base_filters)
        .one()
    )

    # 4) Кол-во по статусам
    by_status = (
        db.query(
            TransactionModel.status,
            func.count().label('count')
        )
        .filter(*base_filters)
        .group_by(TransactionModel.status)
        .all()
    )

    # 5) По банкам отправителя
    by_sender = (
        db.query(
            TransactionModel.sender_bank,
            func.count().label('count')
        )
        .filter(*base_filters)
        .group_by(TransactionModel.sender_bank)
        .all()
    )

    # 6) По банкам получателя
    by_recipient = (
        db.query(
            TransactionModel.recipient_bank,
            func.count().label('count')
        )
        .filter(*base_filters)
        .group_by(TransactionModel.recipient_bank)
        .all()
    )

    return {
        "monthly":           [{"period": p, "count": c} for p, c in monthly],
        "by_type":           [{"type": t,    "count": c} for t, c    in by_type],
        "sums":              {"income": float(sums.income or 0), "expense": float(sums.expense or 0)},
        "by_status":         [{"status": s,  "count": c} for s, c    in by_status],
        "by_sender_bank":    [{"bank": b,    "count": c} for b, c    in by_sender],
        "by_recipient_bank": [{"bank": b,    "count": c} for b, c    in by_recipient],
    }
