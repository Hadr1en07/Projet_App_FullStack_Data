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
from ..routers import team as team_router


@pytest.fixture(scope="function")
def client_user():
    """Configure un client avec un utilisateur standard et quelques joueurs."""
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

    # Limiter le budget pour le test
    team_router.BUDGET = 2000000  # 2 millions

    # Préparer un utilisateur et des joueurs
    with TestingSessionLocal() as db:
        user = crud.create_user(db, schemas.UserCreate(email="user@example.com", password="user123"), is_admin=False)
        p1 = crud.create_player(db, schemas.PlayerCreate(name="P1", cost=1500000, position="Attaquant", club="Club1"))
        p2 = crud.create_player(db, schemas.PlayerCreate(name="P2", cost=1500000, position="Milieu", club="Club2"))
    with TestClient(app) as c:
        # login
        res = c.post("/auth/login", data={"username": "user@example.com", "password": "user123"})
        assert res.status_code == 200
        token = res.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c

    os.close(db_fd)
    os.unlink(db_path)


def test_create_team_and_budget(client_user):
    # Création d'une équipe avec un seul joueur
    response = client_user.post(
        "/team/",
        json={"name": "Mon équipe", "players": [1]},
    )
    assert response.status_code == 201
    team = response.json()
    assert team["name"] == "Mon équipe"
    assert len(team["players"]) == 1

    # Ajouter un second joueur -> dépassement du budget
    response = client_user.post("/team/players", json=[2])
    assert response.status_code == 400
    assert "Budget" in response.json()["detail"]

    # Supprimer le joueur existant et ajouter l'autre
    # Supprimer p1
    response = client_user.delete("/team/players/1")
    assert response.status_code == 200
    assert len(response.json()["players"]) == 0
    # Ajouter p2
    response = client_user.post("/team/players", json=[2])
    assert response.status_code == 200
    assert len(response.json()["players"]) == 1