"""Routes pour la gestion de l'équipe de l'utilisateur.

Un utilisateur possède au plus une équipe.  Les endpoints permettent
de créer cette équipe, d'ajouter ou retirer des joueurs et de
consulter la composition.
"""

import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, crud, auth
from ..dependencies import get_db


# Budget maximum autorisé (récupéré depuis les variables d'environnement)
try:
    BUDGET = int(os.getenv("BUDGET", "100000000"))
except ValueError:
    BUDGET = 100000000


router = APIRouter(prefix="/team", tags=["team"])


@router.get("/", response_model=schemas.TeamOut)
def read_team(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Retourne l'équipe de l'utilisateur courant."""
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return schemas.TeamOut.from_orm(team)


@router.post("/", response_model=schemas.TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: schemas.TeamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Crée une nouvelle équipe pour l'utilisateur courant."""
    team = crud.create_team(db, current_user, team_in, BUDGET)
    return schemas.TeamOut.from_orm(team)


@router.post("/players", response_model=schemas.TeamOut)
def add_players(
    players: List[int],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Ajoute une liste de joueurs à l'équipe existante."""
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    team = crud.add_players_to_team(db, team, players, BUDGET)
    return schemas.TeamOut.from_orm(team)


@router.delete("/players/{player_id}", response_model=schemas.TeamOut)
def remove_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Supprime un joueur de l'équipe."""
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    team = crud.remove_player_from_team(db, team, player_id)
    return schemas.TeamOut.from_orm(team)