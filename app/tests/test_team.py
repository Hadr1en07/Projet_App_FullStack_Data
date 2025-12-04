# app/tests/test_team.py

#Ce fichier permet de tester :
# - création de 2 joueurs avec un budget limité (BUDGET = 2 000 000)
# - création d’une équipe (vide)
# - ajout d’un joueur à l’équipe et vérif que le joueur est bien dedans
# - tester le dépassement de budget
# - tester qu’on ne peut pas gérer une équipe sans être connecté

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.dependencies import get_db
from app import crud, schemas
from app.routers import team as team_router


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
    # Création d'une équipe (sans joueurs au début)
    response = client_user.post(
        "/team/",
        json={"name": "Mon équipe"},
    )
    assert response.status_code == 201
    team = response.json()
    assert team["name"] == "Mon équipe"
    assert team["players"] == []  # équipe vide au départ

    # Ajout d'un premier joueur (id=1)
    response = client_user.post(
        "/team/players",
        json=[1],  
    )
    assert response.status_code == 200
    team = response.json()
    assert len(team["players"]) == 1
    assert team["players"][0]["id"] == 1


# Tester qu’on ne peut pas gérer une équipe sans être connecté
def test_cannot_access_team_without_auth():
    with TestClient(app) as c:
        r = c.get("/team/")
        assert r.status_code in (401, 403)


# Test dépassement de budget
def test_budget_limit(client_user):
    # Création d'une équipe
    r = client_user.post("/team/", json={"name": "Team Budget"})
    assert r.status_code == 201

    # Ajout du premier joueur (id=1)
    r = client_user.post("/team/players", json=[1])
    assert r.status_code == 200
    team = r.json()
    assert len(team["players"]) == 1

    # Ajout du deuxième joueur (id=2) → devrait dépasser le budget
    r = client_user.post("/team/players", json=[2])
    assert r.status_code == 400
    data = r.json()
    assert "budget" in data["detail"].lower() or "Budget" in data["detail"]