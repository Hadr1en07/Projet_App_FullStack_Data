"""Configuration de la base de données et gestion des sessions.

Ce module configure SQLAlchemy pour se connecter à la base de données
PostgreSQL en utilisant des variables d'environnement.  Il expose
``SessionLocal`` pour créer des sessions et ``Base`` pour la
déclaration des modèles.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Récupérer les paramètres de connexion depuis les variables d'environnement
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "myfantasydb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Création de l'engine SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)

# Création de la fabrique de sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()