"""Routes d'authentification.

Ce routeur expose les endpoints pour l'inscription et la connexion des
utilisateurs.  L'enregistrement est ouvert, tandis que le login
retourne un token JWT à utiliser pour les routes protégées.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import schemas, crud, auth
from ..dependencies import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Enregistre un nouvel utilisateur.

    Retourne les informations publiques de l'utilisateur créé.  Un
    utilisateur ayant déjà un compte avec le même email provoque une
    erreur 400.
    """
    # Vérifier l'unicité de l'email via get_user_by_email
    if auth.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = crud.create_user(db, user_in)
    return schemas.UserOut.from_orm(user)


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authentifie un utilisateur et retourne un token JWT."""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return schemas.Token(access_token=access_token, token_type="bearer")