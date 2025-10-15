"""Routes CRUD pour les joueurs.

Les opérations de création, modification et suppression sont
réservées aux administrateurs.  La consultation est ouverte à tous.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, crud, auth
from ..dependencies import get_db


router = APIRouter(prefix="/players", tags=["players"])


@router.get("/", response_model=List[schemas.PlayerOut])
def read_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retourne la liste des joueurs avec pagination."""
    players = crud.get_players(db, skip=skip, limit=limit)
    return [schemas.PlayerOut.from_orm(p) for p in players]


@router.get("/{player_id}", response_model=schemas.PlayerOut)
def read_player(player_id: int, db: Session = Depends(get_db)):
    """Retourne les détails d'un joueur."""
    player = crud.get_player(db, player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return schemas.PlayerOut.from_orm(player)


@router.post("/", response_model=schemas.PlayerOut, status_code=status.HTTP_201_CREATED)
def create_player(
    player_in: schemas.PlayerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin_user),
):
    """Crée un joueur (admin uniquement)."""
    player = crud.create_player(db, player_in)
    return schemas.PlayerOut.from_orm(player)


@router.put("/{player_id}", response_model=schemas.PlayerOut)
def update_player(
    player_id: int,
    update_in: schemas.PlayerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin_user),
):
    """Met à jour un joueur (admin uniquement)."""
    player = crud.get_player(db, player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    player = crud.update_player(db, player, update_in)
    return schemas.PlayerOut.from_orm(player)


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin_user),
):
    """Supprime un joueur (admin uniquement)."""
    player = crud.get_player(db, player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    crud.delete_player(db, player)
    return None