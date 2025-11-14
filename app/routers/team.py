"""Routes pour la gestion de l'équipe de l'utilisateur.

Un utilisateur possède au plus une équipe.
- GET /team                      : consulter l'équipe
- POST /team                     : créer / renommer l'équipe (sans joueurs)
- POST /team/players             : ajouter 1 ou plusieurs joueurs
- DELETE /team/players/{player_id} : retirer un joueur
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from .. import models, schemas, crud, auth
from ..dependencies import get_db, get_current_user


router = APIRouter(prefix="/team", tags=["team"])


# --------- Schéma d'entrée pour /team/players ---------
class AddPlayersPayload(BaseModel):
    # on accepte soit un id unique, soit une liste d'ids
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    return schemas.TeamOut.model_validate(team, from_attributes=True)


@router.post("/", response_model=schemas.TeamOut, status_code=status.HTTP_201_CREATED)
def create_or_reset_team(
    payload: schemas.TeamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
    # compat avec ?local_kw=ui envoyé par l’ancienne version du front
    _ignore: Optional[str] = Query(
        None, alias="local_kw", description="ignored"
    ),
):
    existing = (
        db.query(models.Team)
        .filter(models.Team.owner_id == current_user.id)
        .first()
    )
    try:
        if existing:
            # reset des joueurs + renommage
            if hasattr(existing, "players"):
                existing.players.clear()
            existing.name = payload.name
            db.commit()
            db.refresh(existing)
            team = existing
        else:
            team = models.Team(name=payload.name, owner_id=current_user.id)
            db.add(team)
            db.commit()
            db.refresh(team)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Team name already used",
        )

    return schemas.TeamOut.model_validate(team, from_attributes=True)


@router.post("/players", response_model=schemas.TeamOut)
def add_players(
    payload: AddPlayersPayload,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Ajoute un ou plusieurs joueurs à l'équipe de l'utilisateur."""
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )

    # Normalisation : on obtient toujours une liste d'ids
    ids: List[int] = []
    if payload.player_ids:
        ids = payload.player_ids
    elif payload.player_id is not None:
        ids = [payload.player_id]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No player_id(s) provided",
        )

    # on délègue la logique métier à crud.add_players_to_team
    team = crud.add_players_to_team(db, team, ids)
    return schemas.TeamOut.model_validate(team, from_attributes=True)


@router.delete("/players/{player_id}", response_model=schemas.TeamOut)
def remove_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Supprime un joueur de l'équipe."""
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    team = crud.remove_player_from_team(db, team, player_id)
    return schemas.TeamOut.model_validate(team, from_attributes=True)
