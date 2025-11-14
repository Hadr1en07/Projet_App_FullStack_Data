"""Définition des modèles SQLAlchemy.

Ce module définit les modèles : ``User``, ``Player``, ``Team`` et la
table d'association ``team_players``.  Un utilisateur peut posséder
une unique équipe et chaque équipe est composée de plusieurs joueurs.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship

from .database import Base


# Table d'association pour la relation many‑to‑many entre Team et Player
team_players = Table(
    "team_players",
    Base.metadata,
    Column("team_id", ForeignKey("teams.id"), primary_key=True),
    Column("player_id", ForeignKey("players.id"), primary_key=True),
)


class User(Base):
    """Modèle utilisateur.

    Les utilisateurs sont authentifiés via un email et un mot de passe
    haché.  Le champ ``is_admin`` permet de distinguer un super‑utilisateur
    ayant le droit de créer, modifier et supprimer des joueurs.
    """

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, index=True, nullable=False)
    hashed_password: str = Column(String, nullable=False)
    is_admin: bool = Column(Boolean, default=False)

    team = relationship("Team", uselist=False, back_populates="owner")


class Player(Base):
    """Modèle joueur de football.

    Chaque joueur a un nom, un coût (pour le calcul du budget), un poste
    (attaquant, milieu, défenseur, gardien, etc.) et un club.
    """

    __tablename__ = "players"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=False, index=True)
    cost: int = Column(Integer, nullable=False)
    position: str = Column(String, nullable=False)
    club: str = Column(String, nullable=False)

    teams = relationship(
        "Team",
        secondary=team_players,
        back_populates="players",
    )


class Team(Base):
    """Modèle équipe de fantasy.

    Une équipe appartient à un utilisateur (owner) et possède une liste
    de joueurs via une relation many‑to‑many.  Le nom de l'équipe est
    optionnel et peut être choisi par l'utilisateur.
    """

    __tablename__ = "teams"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=True)
    owner_id: int = Column(Integer, ForeignKey("users.id"), unique=True)

    owner = relationship("User", back_populates="team")
    players = relationship(
        "Player",
        secondary="team_players",   # adapte au nom de ta table d’association
        lazy="selectin"             # ⬅️ charge en un seul SELECT quand on l’utilise
    )