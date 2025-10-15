"""Point d'entrée de l'application FastAPI.

Ce module crée l'instance FastAPI, inclut les différents routeurs
et initialise la base de données au démarrage.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import engine
from . import models
from .routers import auth as auth_router
from .routers import players as players_router
from .routers import team as team_router


# Charger les variables d'environnement depuis .env si présent
load_dotenv()

app = FastAPI(title="MyFantasyLeague", version="1.0.0")

# Activer CORS pour permettre les appels depuis un front externe (optionnel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer les tables si elles n'existent pas
models.Base.metadata.create_all(bind=engine)

# Inclure les routeurs
app.include_router(auth_router.router)
app.include_router(players_router.router)
app.include_router(team_router.router)


@app.get("/")
def read_root():
    return {"message": "Bienvenue sur MyFantasyLeague API"}