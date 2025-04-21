from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.api import auth
from app.db.session import SessionLocal
from app.services.auth import get_user_by_email
from app.utils.security import verify_token
from app.api import transactions


app = FastAPI()

# Разрешаем CORS для фронта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # желательно указать конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статичные файлы
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Подключаем роуты
app.include_router(auth.router)
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


@app.get("/")
async def root():
    return FileResponse("frontend/index.html")


@app.get("/auth")
async def unified_auth_page():
    return FileResponse("frontend/auth.html")

@app.get("/login")
async def redirect_login():
    return RedirectResponse("/auth")

@app.get("/register")
async def redirect_register():
    return RedirectResponse("/auth")

# Вместо него заводим отдельный путь для HTML-страницы
@app.get("/transactions_page", response_class=FileResponse)
async def transactions_page():
    return FileResponse("frontend/transactions.html")

@app.get("/add_transaction")
async def add_transaction_page():
    return FileResponse("frontend/add_transaction.html")


@app.get("/profile")
def get_profile(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        email = payload.get("sub")
        db: Session = SessionLocal()
        user = get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"email": user.email}
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid token or not authenticated")
