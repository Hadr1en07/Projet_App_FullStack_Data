# app/main.py
"""Point d'entrée FastAPI + UI statique."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pathlib

from .database import engine
from . import models
from .routers import auth as auth_router
from .routers import players as players_router
from .routers import team as team_router

app = FastAPI(
    title="MyFantasyLeague",
    description="API Fantasy Football (auth, équipes, joueurs)",
    version="1.0.0",
)

# CORS (ok pour demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fichiers statiques et UI
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/ui", response_class=HTMLResponse, tags=["ui"])
def ui_root():
    p = pathlib.Path("app/templates/index.html")
    return p.read_text(encoding="utf-8")

# DB : créer les tables (si besoin)
models.Base.metadata.create_all(bind=engine)

# Routers
app.include_router(auth_router.router)
app.include_router(players_router.router)
app.include_router(team_router.router)

@app.get("/", tags=["default"])
def read_root():
    return {"message": "Bienvenue sur MyFantasyLeague API"}
