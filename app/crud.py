"""Fonctions d'accès aux données (CRUD).

Ce module regroupe les opérations courantes sur les modèles :
création d'utilisateurs, gestion des joueurs et des équipes.  Il
implémente les règles métier comme la vérification du budget lors de
l'ajout de joueurs dans une équipe.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from . import models, schemas, auth


def create_user(db: Session, user_in: schemas.UserCreate, is_admin: bool = False) -> models.User:
    """Crée un nouvel utilisateur dans la base.

    Args:
        db: session SQLAlchemy
        user_in: schéma contenant l'email et le mot de passe
        is_admin: flag indiquant si l'utilisateur est administrateur

    Returns:
        L'utilisateur créé.
    """
    hashed_password = auth.get_password_hash(user_in.password)
    db_user = models.User(email=user_in.email, hashed_password=hashed_password, is_admin=is_admin)
    db.add(db_user)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_player(db: Session, player_id: int) -> Optional[models.Player]:
    return db.query(models.Player).filter(models.Player.id == player_id).first()


def get_players(db: Session, skip: int = 0, limit: int = 100) -> List[models.Player]:
    return db.query(models.Player).offset(skip).limit(limit).all()


def create_player(db: Session, player_in: schemas.PlayerCreate) -> models.Player:
    db_player = models.Player(**player_in.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def update_player(db: Session, db_player: models.Player, update_in: schemas.PlayerUpdate) -> models.Player:
    for field, value in update_in.dict(exclude_unset=True).items():
        setattr(db_player, field, value)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def delete_player(db: Session, db_player: models.Player) -> None:
    db.delete(db_player)
    db.commit()


def get_team_by_owner(db: Session, owner_id: int) -> Optional[models.Team]:
    return db.query(models.Team).filter(models.Team.owner_id == owner_id).first()


def create_team(db: Session, owner: models.User, team_in: schemas.TeamCreate, budget: int) -> models.Team:
    """Crée une équipe pour l'utilisateur donné.

    Lève une erreur si l'utilisateur possède déjà une équipe ou si le budget est dépassé.
    """
    existing_team = get_team_by_owner(db, owner.id)
    if existing_team:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a team")
    # Créer l'équipe
    team = models.Team(name=team_in.name, owner_id=owner.id)
    db.add(team)
    db.commit()
    db.refresh(team)
    # Ajouter les joueurs si fournis
    if team_in.players:
        add_players_to_team(db, team, team_in.players, budget)
    return team


def add_players_to_team(db: Session, team: models.Team, player_ids: List[int], budget: int) -> models.Team:
    """Ajoute une liste de joueurs à l'équipe après validation du budget.

    Args:
        db: session SQLAlchemy
        team: équipe à mettre à jour
        player_ids: liste des IDs de joueurs à ajouter
        budget: budget maximum autorisé

    Returns:
        L'équipe mise à jour.
    """
    # Ajouter chaque joueur s'il n'est pas déjà présent
    for pid in player_ids:
        player = get_player(db, pid)
        if not player:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Player {pid} not found")
        if player not in team.players:
            team.players.append(player)
    # Vérifier le budget
    total_cost = sum(p.cost for p in team.players)
    if total_cost > budget:
        # Supprimer les joueurs ajoutés pour ne pas laisser un état incohérent
        for pid in player_ids:
            player = get_player(db, pid)
            if player in team.players:
                team.players.remove(player)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Budget exceeded")
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def remove_player_from_team(db: Session, team: models.Team, player_id: int) -> models.Team:
    """Retire un joueur de l'équipe s'il est présent."""
    player = get_player(db, player_id)
    if not player or player not in team.players:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not in team")
    team.players.remove(player)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team