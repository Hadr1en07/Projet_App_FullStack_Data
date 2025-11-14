"""Schémas Pydantic pour la validation et la sérialisation.

Ces classes définissent la structure des données attendues et retournées
par l'API.  Les modèles d'entrée (``Create``, ``Update``) et de sortie
(``Out``) sont séparés pour éviter d'exposer des informations sensibles
(comme les mots de passe hachés).
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserOut(UserBase):
    id: int
    is_admin: bool

    class Config:
        orm_mode = True


class PlayerBase(BaseModel):
    name: str
    cost: int
    position: str
    club: str


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    cost: Optional[int] = None
    position: Optional[str] = None
    club: Optional[str] = None


class PlayerOut(BaseModel):
    id: int
    name: str
    club: str
    position: str
    cost: Optional[float] = None

    class Config:
        from_attributes = True


class TeamBase(BaseModel):
    name: Optional[str] = None


class TeamCreate(BaseModel):
    name: str

class TeamOut(BaseModel):
    id: int
    name: str
    owner_id: int
    players: List[PlayerOut] = []

    class Config:
        from_attributes = True