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

# Chemin vers ton CSV (change ici si ton fichier a un autre nom)
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
    "Goalkeeper": "GK",
    "GK": "GK",
    "Goalie": "GK",

    "Defender": "DEF",
    "Centre-Back": "DEF",
    "Center Back": "DEF",
    "Left-Back": "DEF",
    "Right-Back": "DEF",
    "Left Back": "DEF",
    "Right Back": "DEF",
    "CB": "DEF",
    "LB": "DEF",
    "RB": "DEF",

    "Midfielder": "MID",
    "Central Midfield": "MID",
    "Attacking Midfield": "MID",
    "Defensive Midfield": "MID",
    "CM": "MID",
    "CAM": "MID",
    "CDM": "MID",
    "LM": "MID",
    "RM": "MID",

    "Forward": "FWD",
    "Striker": "FWD",
    "Winger": "FWD",
    "Left Winger": "FWD",
    "Right Winger": "FWD",
    "LW": "FWD",
    "RW": "FWD",
    "ST": "FWD",
}


def normalize_position(raw_pos: str) -> str:
    raw_pos = (raw_pos or "").strip()
    if not raw_pos:
        return "MID"
    # Essai direct
    if raw_pos in POSITION_MAP:
        return POSITION_MAP[raw_pos]
    # Essai avec capitalisation standard
    key = raw_pos.title()
    if key in POSITION_MAP:
        return POSITION_MAP[key]
    # Essai sur version upper
    key2 = raw_pos.upper()
    if key2 in POSITION_MAP:
        return POSITION_MAP[key2]
    # Fallback : milieux par défaut
    return "MID"


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


def _set_price_field(p: Player, value: float) -> None:
    """
    Dépose le prix dans le 1er champ existant parmi
    price_m / price / cost_m / cost / value.
    """
    for field in ("price_m", "price", "cost_m", "cost", "value"):
        if hasattr(Player, field):
            setattr(p, field, value)
            return
    # Si aucun champ connu, on crée 'price' dynamiquement (idéalement adapter le modèle)
    setattr(p, "price", value)


def _parse_float(raw: str | None, default: float = 10.0) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def iter_players_from_csv() -> Iterable[Tuple[str, str, str, float]]:
    """
    Lit le CSV CSV_PATH et produit des tuples (name, club, pos, cost).

    On ne garde que les colonnes utiles. Le reste est ignoré.
    On essaie plusieurs noms de colonnes possibles pour être robuste.
    """
    if not os.path.exists(CSV_PATH):
        print(f"[seed] CSV not found: {CSV_PATH}, aucun joueur importé.")
        return []

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"[seed] CSV chargé: {CSV_PATH} ({len(rows)} lignes)")

    for row in rows:
        # --- Name ---
        name = (
            row.get("name")
            or row.get("player_name")
            or row.get("short_name")
            or row.get("full_name")
        )
        if not name:
            continue

        # --- Club ---
        club = (
            row.get("club")
            or row.get("club_name")
            or row.get("team")
            or row.get("club_team")
        )
        if not club:
            club = "Unknown"

        # --- League (optionnel, pour filtrer) ---
        league = (
            row.get("league")
            or row.get("league_name")
            or row.get("competition")
        )
        # Si tu veux filtrer sur les 5 grands championnats, décommente :
        # BIG5 = {"Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"}
        # if league and league not in BIG5:
        #     continue

        # --- Position brute ---
        raw_pos = (
            row.get("position")
            or row.get("pos")
            or row.get("primary_position")
            or row.get("role")
        )
        norm_pos = normalize_position(raw_pos)

        # --- Cost ---
        # Essaye plusieurs colonnes possibles pour la valeur de marché :
        cost_raw = (
            row.get("cost")
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
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # -----------------------------------------------------------------
        # 1) Utilisateurs par défaut
        # -----------------------------------------------------------------
        if not get_user_by_email(db, "admin@example.com"):
            db.add(
                User(
                    email="admin@example.com",
                    hashed_password=hash_password("admin123"),
                    is_admin=True,
                )
            )

        if not get_user_by_email(db, "user@example.com"):
            db.add(
                User(
                    email="user@example.com",
                    hashed_password=hash_password("user123"),
                    is_admin=False,
                )
            )

        db.commit()

        # -----------------------------------------------------------------
        # 2) Joueurs
        # -----------------------------------------------------------------
        if db.query(Player).count() == 0:
            print("[seed] La table Player est vide, import depuis CSV…")
            for name, club, pos, price in iter_players_from_csv():
                p = Player(
                    name=name,
                    club=club,
                    position=_coerce_position(pos),
                )
                _set_price_field(p, price)
                db.add(p)

            db.commit()
            print("[seed] Import des joueurs terminé ✅")
        else:
            print("[seed] Joueurs déjà présents, skip import CSV.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
