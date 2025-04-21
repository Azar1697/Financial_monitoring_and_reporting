# app/api/reports.py
from datetime import datetime, date
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy.orm import Session

from app.db.models.transaction import Transaction as Tx
from app.schemas.transaction import TransactionStatus, TransactionType
from app.dependencies.oauth2 import oauth2_scheme
from app.db.session import SessionLocal
from app.utils.security import verify_token
from app.services.auth import get_user_by_email

router = APIRouter()

# Путь к TTF‑шрифту (поддерживает кириллицу)
FONT_PATH = Path(__file__).parent.parent / "static" / "fonts" / "DejaVuSans.ttf"
FONT_NAME = "DejaVuSans"

# ────────────────────────── DB session ──────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─────────── фильтр (тот же, что в  /transactions) ────────────
def filtered_q(
    user_id: int,
    db: Session,
    start: Optional[date], end: Optional[date],
    status_: Optional[TransactionStatus],
    tx_type: Optional[TransactionType],
    min_amount: Optional[float], max_amount: Optional[float],
    category: Optional[str],
    s_bank: Optional[str],
    r_bank: Optional[str],
    inn: Optional[str]
):
    q = db.query(Tx).filter(Tx.user_id == user_id)

    if start:
        q = q.filter(Tx.date_time >= datetime.combine(start, datetime.min.time()))
    if end:
        q = q.filter(Tx.date_time <= datetime.combine(end, datetime.max.time()))
    if status_:
        q = q.filter(Tx.status == status_)
    if tx_type:
        q = q.filter(Tx.transaction_type == tx_type)
    if min_amount is not None:
        q = q.filter(Tx.amount >= min_amount)
    if max_amount is not None:
        q = q.filter(Tx.amount <= max_amount)
    if category:
        q = q.filter(Tx.category == category)
    if s_bank:
        q = q.filter(Tx.sender_bank == s_bank)
    if r_bank:
        q = q.filter(Tx.recipient_bank == r_bank)
    if inn:
        q = q.filter(Tx.recipient_inn == inn)

    return q.all()

# ───────────────────── /reports ─────────────────────
@router.get("/reports", summary="Скачать отчёт (PDF или Excel)")
def download_report(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),

    start: Optional[date] = Query(None),
    end:   Optional[date] = Query(None),
    status_: Optional[TransactionStatus] = Query(None, alias="status"),
    transaction_type: Optional[TransactionType] = Query(None),
    min_amount: Optional[float] = Query(None, ge=0),
    max_amount: Optional[float] = Query(None, ge=0),
    category: Optional[str]    = Query(None),
    sender_bank: Optional[str] = Query(None),
    recipient_bank: Optional[str] = Query(None),
    recipient_inn: Optional[str]  = Query(None),

    format: str = Query("pdf", regex="^(pdf|xlsx)$")   # <- regex вместо pattern
):
    # ---------- auth ----------
    payload = verify_token(token)
    user = get_user_by_email(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = filtered_q(
        user.id, db,
        start, end, status_, transaction_type,
        min_amount, max_amount,
        category, sender_bank, recipient_bank, recipient_inn
    )

    if not data:
        raise HTTPException(status_code=404, detail="Нет данных за выбранный период")

    # ---------- DataFrame ----------
    df = pd.DataFrame([{
        "ID": t.id,
        "Дата / время": t.date_time.strftime("%d.%m.%Y %H:%M"),
        "Тип": t.transaction_type.value,
        "Категория": t.category or "",
        "Сумма": f"{t.amount:.2f}",
        "Статус": t.status.value,
        "Банк получателя": t.recipient_bank or "",
        "ИНН получателя": t.recipient_inn
    } for t in data])

    # ---------- Excel ----------
    if format == "xlsx":
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Report")
        buf.seek(0)
        fname = f"report_{datetime.utcnow():%Y%m%d_%H%M%S}.xlsx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename=\"{fname}\"'}
        )

    # ---------- PDF ----------
    # регистрируем шрифт (один раз за процесс)
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        if not FONT_PATH.exists():
            raise HTTPException(status_code=500, detail="Шрифт DejaVuSans.ttf не найден")
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH)))

    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=landscape(A4))
    pdf.setFont(FONT_NAME, 9)

    # вычисляем ширину колонок
    cols = list(df.columns)
    col_w = []
    for col in cols:
        max_len = max(len(str(x)) for x in df[col].tolist() + [col])
        # 6 px ≈ средняя ширина символа шрифтом 9 pt
        col_w.append(max(60, min(140, max_len * 6)))

    x0, y0 = 40, A4[0] - 40
    row_h  = 14

    # --- заголовок таблицы ---
    x = x0
    for w, name in zip(col_w, cols):
        pdf.drawString(x, y0, name)
        x += w
    pdf.line(x0, y0 - 2, x0 + sum(col_w), y0 - 2)

    # --- строки ---
    y = y0
    for _, row in df.iterrows():
        y -= row_h
        if y < 40:                       # новая страница
            pdf.showPage()
            pdf.setFont(FONT_NAME, 9)
            y = y0
        x = x0
        for w, val in zip(col_w, row):
            pdf.drawString(x, y, str(val))
            x += w

    pdf.save()
    buf.seek(0)

    fname = f"report_{datetime.utcnow():%Y%m%d_%H%M%S}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename=\"{fname}\"'}
    )
