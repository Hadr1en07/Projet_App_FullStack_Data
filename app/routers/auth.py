# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..dependencies import get_db
from .. import models, schemas
from ..auth import verify_password, hash_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Register (JSON) ---
@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(email=user_in.email, hashed_password=hash_password(user_in.password))
    db.add(user); db.commit(); db.refresh(user)
    return user

# --- Login: accepte FORM ou JSON ---
class LoginJSON(BaseModel):
    username: EmailStr
    password: str

@router.post("/login", response_model=schemas.Token)
async def login(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # 1) tenter form-data (Swagger par défaut)
    username = getattr(form_data, "username", None)
    password = getattr(form_data, "password", None)

    # 2) sinon, tenter JSON
    if not username or not password:
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")

    user = db.query(models.User).filter(models.User.email == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = create_access_token(subject=user.email)
    return {"access_token": token, "token_type": "bearer"}
