"""Fonctions d'authentification et de sécurité.

Ce module centralise la création et la vérification des tokens
JWT, la gestion des mots de passe hachés et les dépendances
FastAPI pour récupérer l'utilisateur courant.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models, schemas
from .database import SessionLocal


# Récupération des variables d'environnement
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Initialisation du contexte de hachage pour les mots de passe
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Schéma OAuth2 pour récupérer le token dans l'en‑tête Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def get_password_hash(password: str) -> str:
    """Génère un haché pour un mot de passe donné."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT avec une date d'expiration.

    Args:
        data: les données à inclure dans le payload du token.
        expires_delta: durée de validité du token.

    Returns:
        Le token JWT sous forme de chaîne.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Récupère un utilisateur par son email."""
    return db.query(models.User).filter(models.User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Authentifie un utilisateur.

    Args:
        db: session SQLAlchemy
        email: email saisi
        password: mot de passe saisi

    Returns:
        L'utilisateur si les identifiants sont corrects, sinon ``None``.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(SessionLocal),
) -> models.User:
    """Dépendance FastAPI pour récupérer l'utilisateur courant à partir du token.

    Lève une exception HTTP 401 si le token est invalide ou si l'utilisateur n'existe pas.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")  # subject of the token
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(db, token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Vérifie que l'utilisateur courant est actif.

    Dans cette implémentation, tous les utilisateurs enregistrés sont considérés comme actifs.
    Cette fonction peut être étendue pour vérifier un champ ``is_active``.
    """
    return current_user


async def get_current_admin_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Vérifie que l'utilisateur courant est administrateur."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user