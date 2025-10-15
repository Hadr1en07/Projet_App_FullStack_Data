"""Script de population de la base de données.

Ce script est exécuté au démarrage du conteneur Docker (via
docker-compose).  Il attend que la base de données soit accessible,
puis crée les tables, un utilisateur administrateur et quelques
joueurs emblématiques pour permettre de tester l'application.
"""

import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .database import DATABASE_URL, Base, SessionLocal
from . import crud, models, schemas

# Charger les variables d'environnement
load_dotenv()


def wait_for_db(engine) -> None:
    """Attendre que la base de données soit prête."""
    retries = 10
    while retries > 0:
        try:
            # Tenter de se connecter
            with engine.connect() as connection:
                return
        except Exception:
            retries -= 1
            time.sleep(1)
    raise RuntimeError("Database not ready")


def seed():
    engine = create_engine(DATABASE_URL)
    # Attendre la base
    wait_for_db(engine)
    # Créer les tables
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    # Créer admin si non existant
    admin_email = "admin@example.com"
    from . import auth  # import local pour éviter dépendances circulaires
    if not auth.get_user_by_email(db, admin_email):
        admin_schema = schemas.UserCreate(email=admin_email, password="admin123")
        crud.create_user(db, admin_schema, is_admin=True)
    # Créer un utilisateur standard
    user_email = "user@example.com"
    if not auth.get_user_by_email(db, user_email):
        user_schema = schemas.UserCreate(email=user_email, password="user123")
        crud.create_user(db, user_schema, is_admin=False)
    # Ajouter des joueurs de démonstration si la table est vide
    if not db.query(models.Player).first():
        players = [
            schemas.PlayerCreate(name="Kylian Mbappé", cost=15000000, position="Attaquant", club="Paris SG"),
            schemas.PlayerCreate(name="Erling Haaland", cost=14000000, position="Attaquant", club="Man City"),
            schemas.PlayerCreate(name="Kevin De Bruyne", cost=12000000, position="Milieu", club="Man City"),
            schemas.PlayerCreate(name="Lionel Messi", cost=13000000, position="Attaquant", club="Inter Miami"),
            schemas.PlayerCreate(name="Thibaut Courtois", cost=8000000, position="Gardien", club="Real Madrid"),
            schemas.PlayerCreate(name="Achraf Hakimi", cost=9000000, position="Défenseur", club="Paris SG"),
            schemas.PlayerCreate(name="Jude Bellingham", cost=11000000, position="Milieu", club="Real Madrid"),
        ]
        for p in players:
            crud.create_player(db, p)
    db.close()


if __name__ == "__main__":
    seed()