# app/seed.py
import time
from typing import Any
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from passlib.context import CryptContext

from app.database import Base, engine, SessionLocal
from app.models import User, Player

load_dotenv()

# Hash avec Argon2 (pas de bcrypt ici)
_pwd = CryptContext(schemes=["argon2"], deprecated="auto")
def hash_password(p: str) -> str:
    return _pwd.hash(p)

def wait_for_db() -> None:
    """Attend que la BDD soit joignable via engine."""
    retries = 30
    while retries > 0:
        try:
            with engine.connect() as _:
                return
        except Exception:
            retries -= 1
            time.sleep(1)
    raise RuntimeError("Database not ready")

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# (name, club, position, price_in_millions)
PLAYERS = [
    ("Kylian Mbappé",  "PSG",         "FWD", 18.0),
    ("Erling Haaland", "Man City",    "FWD", 20.0),
    ("Jude Bellingham","Real Madrid", "MID", 16.0),
    ("Kevin De Bruyne","Man City",    "MID", 14.0),
    ("Declan Rice",    "Arsenal",     "MID", 11.0),
    ("Virgil van Dijk","Liverpool",   "DEF", 10.0),
    ("Achraf Hakimi",  "PSG",         "DEF",  9.0),
    ("Rúben Dias",     "Man City",    "DEF",  9.5),
    ("Theo Hernandez", "AC Milan",    "DEF",  8.5),
    ("Mike Maignan",   "AC Milan",    "GK",   7.0),
    ("Ederson",        "Man City",    "GK",   6.5),
]

def _set_price_field(p: Player, value: float) -> None:
    """Dépose le prix dans le 1er champ existant parmi price_m/price/cost_m/cost/value."""
    for field in ("price_m", "price", "cost_m", "cost", "value"):
        if hasattr(Player, field):
            setattr(p, field, value)
            return
    # Si aucun champ connu, on crée 'price' dynamiquement (bonne pratique: adapter le modèle)
    setattr(p, "price", value)

def _coerce_position(pos_text: str) -> Any:
    """
    Si Player.position est un Enum SQLAlchemy, convertit "FWD" -> Enum("FWD").
    Sinon, renvoie la chaîne telle quelle.
    """
    if hasattr(Player, "position"):
        col = getattr(Player, "position")
        coltype = getattr(col, "type", None)
        enum_cls = getattr(coltype, "enum_class", None)
        if enum_cls is not None:
            try:
                return enum_cls(pos_text)
            except Exception:
                # Valeur par défaut sûre
                return list(enum_cls)[0]
    return pos_text  # string simple

def seed():
    wait_for_db()
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Admin
        if not get_user_by_email(db, "admin@example.com"):
            db.add(User(
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                is_admin=True
            ))

        # User standard
        if not get_user_by_email(db, "user@example.com"):
            db.add(User(
                email="user@example.com",
                hashed_password=hash_password("user123"),
                is_admin=False
            ))

        # Joueurs
        if db.query(Player).count() == 0:
            for name, club, pos, price in PLAYERS:
                p = Player(
                    name=name,
                    club=club,
                    position=_coerce_position(pos),
                )
                _set_price_field(p, price)
                db.add(p)

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
