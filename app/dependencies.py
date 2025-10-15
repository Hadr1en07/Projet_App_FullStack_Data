"""Définition des dépendances communes pour l'API FastAPI.

Ce module fournit une fonction ``get_db`` qui crée une session
SQLAlchemy et la ferme automatiquement après l'utilisation.  D'autres
dépendances (comme ``get_current_user``) sont exposées via
``app.auth``.
"""

from typing import Generator
from .database import SessionLocal


def get_db() -> Generator:
    """Fournit une session de base de données et la ferme après usage.

    Yields:
        Session: une session SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()