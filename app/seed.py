# app/seed.py
"""
Script de seed pour l'application :

- Attend que la base Postgres soit prête
- Crée les tables (Base.metadata.create_all)
- Crée deux utilisateurs par défaut :
    - admin@example.com / admin123 (is_admin=True)
    - user@example.com  / user123  (is_admin=False)
- Charge des joueurs depuis un CSV brut (app/data/players_seed.csv)
  et les insère dans la table Player avec un prix et un poste normalisés.
"""

import os
import time
import csv
from typing import Any, Iterable, Tuple

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.models import User, Player

load_dotenv()

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------

# Chemin vers ton CSV
CSV_PATH = os.getenv("PLAYERS_CSV", "app/data/players_seed.csv")

# Hash de mot de passe (Argon2)
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


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


# ---------------------------------------------------------------------
# Normalisation des joueurs
# ---------------------------------------------------------------------

# Mapping de position brute -> position simplifiée pour le jeu
POSITION_MAP = {
    "Goalkeeper": "GK", "GK": "GK", "Goalie": "GK",
    "Defender": "DEF", "Centre-Back": "DEF", "Center Back": "DEF",
    "Left-Back": "DEF", "Right-Back": "DEF", "Left Back": "DEF",
    "Right Back": "DEF", "CB": "DEF", "LB": "DEF", "RB": "DEF",
    "Midfielder": "MID", "Central Midfield": "MID", "Attacking Midfield": "MID",
    "Defensive Midfield": "MID", "CM": "MID", "CAM": "MID", "CDM": "MID",
    "LM": "MID", "RM": "MID",
    "Forward": "FWD", "Striker": "FWD", "Winger": "FWD",
    "Left Winger": "FWD", "Right Winger": "FWD", "LW": "FWD",
    "RW": "FWD", "ST": "FWD",
}


def normalize_position(raw_pos: str) -> str:
    raw_pos = (raw_pos or "").strip()
    if not raw_pos:
        return "MID"
    if raw_pos in POSITION_MAP:
        return POSITION_MAP[raw_pos]
    key = raw_pos.title()
    if key in POSITION_MAP:
        return POSITION_MAP[key]
    key2 = raw_pos.upper()
    if key2 in POSITION_MAP:
        return POSITION_MAP[key2]
    return "MID"


def _coerce_position(pos_text: str) -> Any:
    if hasattr(Player, "position"):
        col = getattr(Player, "position")
        coltype = getattr(col, "type", None)
        enum_cls = getattr(coltype, "enum_class", None)
        if enum_cls is not None:
            try:
                return enum_cls(pos_text)
            except Exception:
                return list(enum_cls)[0]
    return pos_text


def _set_price_field(p: Player, value: float) -> None:
    for field in ("price_m", "price", "cost_m", "cost", "value"):
        if hasattr(Player, field):
            setattr(p, field, value)
            return
    setattr(p, "price", value)


def _parse_float(raw: str | None, default: float = 10.0) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def iter_players_from_csv() -> Iterable[Tuple[str, str, str, float]]:
    if not os.path.exists(CSV_PATH):
        print(f"[seed] CSV not found: {CSV_PATH}, aucun joueur importé.")
        return []

    # 'utf-8-sig' gère le BOM (Byte Order Mark) souvent ajouté par Excel
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"[seed] CSV chargé: {CSV_PATH} ({len(rows)} lignes)")

    for row in rows:
        # --- Name ---
        name = (
            row.get("Name")             # <--- MAJUSCULE AJOUTÉE
            or row.get("name")
            or row.get("player_name")
            or row.get("short_name")
            or row.get("full_name")
        )
        if not name:
            continue

        # --- Club ---
        club = (
            row.get("Club")             # <--- MAJUSCULE AJOUTÉE
            or row.get("club")
            or row.get("club_name")
            or row.get("team")
            or row.get("club_team")
        )
        if not club:
            club = "Unknown"

        # --- Position ---
        raw_pos = (
            row.get("Position")         # <--- MAJUSCULE AJOUTÉE
            or row.get("position")
            or row.get("pos")
            or row.get("primary_position")
            or row.get("role")
        )
        norm_pos = normalize_position(raw_pos)

        # --- Cost ---
        cost_raw = (
            row.get("Market Value")     # <--- MAJUSCULES AJOUTÉES
            or row.get("cost")
            or row.get("price")
            or row.get("market_value")
            or row.get("market_value_million_eur")
            or row.get("value_in_million_euros")
        )
        cost = _parse_float(cost_raw, default=10.0)

        yield name, club, norm_pos, cost


def seed():
    """Point d'entrée du seed."""
    wait_for_db()
    # On s'assure que les tables existent
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 1) Utilisateurs par défaut
        if not get_user_by_email(db, "admin@example.com"):
            db.add(User(email="admin@example.com", hashed_password=hash_password("admin123"), is_admin=True))
        if not get_user_by_email(db, "user@example.com"):
            db.add(User(email="user@example.com", hashed_password=hash_password("user123"), is_admin=False))
        db.commit()

        # 2) Joueurs
        # On vérifie si la table est vide pour ne pas importer en double
        if db.query(Player).count() == 0:
            print("[seed] La table Player est vide, import depuis CSV…")
            count = 0
            for name, club, pos, price in iter_players_from_csv():
                p = Player(
                    name=name,
                    club=club,
                    position=_coerce_position(pos),
                )
                _set_price_field(p, price)
                db.add(p)
                count += 1
            db.commit()
            print(f"[seed] Import terminé : {count} joueurs ajoutés ✅")
        else:
            print("[seed] Joueurs déjà présents, pas d'import.")

    except Exception as e:
        print(f"[seed] ERREUR : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()