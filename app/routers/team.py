# app/routers/team.py
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from .. import models, schemas, crud, auth
from ..dependencies import get_db 

# On récupère le budget (1 milliard si défini dans .env)
BUDGET = int(os.getenv("BUDGET", "100000000"))

router = APIRouter(prefix="/team", tags=["team"])

# --- Fonction utilitaire pour calculer le budget ---
def format_team_response(team: models.Team) -> schemas.TeamOut:
    """Calcule le budget restant et retourne l'objet TeamOut complet."""
    if not team:
        return None
    
    # Calcul du coût total des joueurs
    total_cost = sum(p.cost for p in team.players)
    budget_left = BUDGET - total_cost

    # On construit la réponse manuellement avec les champs calculés
    return schemas.TeamOut(
        id=team.id,
        name=team.name,
        owner_id=team.owner_id,
        players=team.players,
        budget_left=budget_left,
        total_budget=BUDGET
    )

# --- Endpoints ---

@router.get("/", response_model=schemas.TeamOut)
def read_team(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        # ANCIEN CODE QUI BLOQUE :
        # raise HTTPException(status_code=404, detail="Team not found")
        
        # NOUVEAU CODE : On renvoie une équipe vide par défaut
        return schemas.TeamOut(
            id=-1,              # ID fictif
            name="",            # Nom vide
            owner_id=current_user.id,
            players=[],         # Pas de joueurs
            budget_left=BUDGET, # On lui donne tout le budget !
            total_budget=BUDGET
        )
    return format_team_response(team)


@router.post("/", response_model=schemas.TeamOut, status_code=status.HTTP_201_CREATED)
def create_or_reset_team(
    payload: schemas.TeamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    existing = db.query(models.Team).filter(models.Team.owner_id == current_user.id).first()
    try:
        if existing:
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
        raise HTTPException(status_code=409, detail="Team name already used")

    return format_team_response(team)


@router.post("/players", response_model=schemas.TeamOut)
def add_players(
    players: List[int],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Note : crud.add_players_to_team vérifie déjà le BUDGET, 
    # mais on utilise ici la variable globale de ce fichier.
    team = crud.add_players_to_team(db, team, players, BUDGET)
    return format_team_response(team)


@router.delete("/players/{player_id}", response_model=schemas.TeamOut)
def remove_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    team = crud.get_team_by_owner(db, current_user.id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team = crud.remove_player_from_team(db, team, player_id)
    return format_team_response(team)