import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..main import app
from ..database import Base
from ..dependencies import get_db
from .. import crud, schemas


@pytest.fixture(scope="function")
def client_admin():
    """Configure un client avec un utilisateur admin pré‑créé."""
    db_fd, db_path = tempfile.mkstemp()
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Créer un admin et un token
    with TestingSessionLocal() as db:
        admin_schema = schemas.UserCreate(email="admin@example.com", password="admin123")
        admin_user = crud.create_user(db, admin_schema, is_admin=True)

    with TestClient(app) as c:
        # se connecter en tant qu'admin
        res = c.post(
            "/auth/login",
            data={"username": "admin@example.com", "password": "admin123"},
        )
        assert res.status_code == 200
        token = res.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c

    os.close(db_fd)
    os.unlink(db_path)


def test_create_read_update_delete_player(client_admin):
    # Créer un joueur
    response = client_admin.post(
        "/players/",
        json={"name": "Test Player", "cost": 1000000, "position": "Milieu", "club": "Test FC"},
    )
    assert response.status_code == 201
    player = response.json()
    assert player["name"] == "Test Player"

    player_id = player["id"]

    # Lire le joueur
    response = client_admin.get(f"/players/{player_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Player"

    # Mettre à jour le joueur
    response = client_admin.put(
        f"/players/{player_id}",
        json={"cost": 2000000},
    )
    assert response.status_code == 200
    assert response.json()["cost"] == 2000000

    # Supprimer le joueur
    response = client_admin.delete(f"/players/{player_id}")
    assert response.status_code == 204

    # Vérifier qu'il n'existe plus
    response = client_admin.get(f"/players/{player_id}")
    assert response.status_code == 404