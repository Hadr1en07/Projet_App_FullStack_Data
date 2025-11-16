"""Routes pour la gestion de l'équipe de l'utilisateur.

Un utilisateur possède au plus une équipe.
- GET /team              : consulter l'équipe
- POST /team             : créer / réinitialiser l'équipe (sans joueurs)
- POST /team/players     : ajouter 1 ou N joueurs (body: [1, 2, 3])
- DELETE /team/players/{player_id} : retirer un joueur
"""

#commentaire test
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from .. import models, schemas, crud, auth
from ..dependencies import get_db 

BUDGET = int(os.getenv("BUDGET", "100000000"))  # 100 M€ par défaut

router = APIRouter(prefix="/team", tags=["team"])


# --------- Schéma d'entrée optionnel (si besoin plus tard) ---------
class AddPlayersPayload(BaseModel):
    # on pourrait l’utiliser plus tard si on voulait accepter un body {player_ids: [...]}
    player_id: Optional[int] = None
    player_ids: Optional[List[int]] = None


# --------- Endpoints ---------

@router.get("/", response_model=schemas.TeamOut)
def read_team(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    # Pydantic v2 -> from_attributes=True
    return schemas.TeamOut.model_validate(team, from_attributes=True)


@router.post("/", response_model=schemas.TeamOut, status_code=status.HTTP_201_CREATED)
def create_or_reset_team(
    payload: schemas.TeamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    existing = db.query(models.Team).filter(models.Team.owner_id == current_user.id).first()

    try:
        if existing:
            # réinitialisation : on vide les joueurs et on change le nom
            if hasattr(existing, "players"):
                existing.players.clear()
            existing.name = payload.name
            db.commit()
            db.refresh(existing)
            team = existing
        else:
            # création
            team = models.Team(name=payload.name, owner_id=current_user.id)
            db.add(team)
            db.commit()
            db.refresh(team)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Team name already used")

    return schemas.TeamOut.model_validate(team, from_attributes=True)


@router.post("/players", response_model=schemas.TeamOut)
def add_players(
    players: List[int],  # body: [1,2,3]
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    team = crud.add_players_to_team(db, team, players, BUDGET)
    return schemas.TeamOut.model_validate(team, from_attributes=True)


@router.delete("/players/{player_id}", response_model=schemas.TeamOut)
def remove_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    team = crud.remove_player_from_team(db, team, player_id)
    return schemas.TeamOut.model_validate(team, from_attributes=True)
