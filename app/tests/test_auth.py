# app/tests/test_auth.py

#Ce fichier permet de tester :
# - la gestion d’utilisateurs
# - la génération de token
# - la gestion d’erreur HTTP côté auth

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.dependencies import get_db
from app import crud, schemas, models


@pytest.fixture(scope="function")
def client():
    """Configure un client TestClient avec une base SQLite temporaire."""
    # Créer une base de données temporaire
    db_fd, db_path = tempfile.mkstemp()
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Créer les tables
    Base.metadata.create_all(bind=engine)

    # Override de la dépendance get_db
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # Nettoyage
    os.close(db_fd)
    os.unlink(db_path)


def test_register_and_login(client):
    # Enregistrer un nouvel utilisateur
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["is_admin"] is False

    # Essayer de se connecter avec le bon mot de passe
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Connexion avec un mauvais mot de passe
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "wrong"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data