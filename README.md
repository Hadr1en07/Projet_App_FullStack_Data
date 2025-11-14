# Projet MyFantasyLeague

MyFantasyLeague est une application de type _fantasy football_ développée en Python avec [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) et [PostgreSQL](https://www.postgresql.org/).  Le projet a été réalisé dans le cadre d'un cours appelé "Application Full Stack Data" enseigné par Monsieur Morgan Courivaud à ESIEE Paris. Ce cours est enseigné en dernière année d'école ingénieur (5ème année) pour l'ensemble de la filière "Data Science & Intelligence Artificelle"

### Projet réalisé par Hadrien DEJONGHE & Esteban NABONNE - E5 DSIA

Il respecte l'intégralité des exigences demandées :

## 🎯 Objectifs

L'application permet à chaque utilisateur de créer son **équipe de rêve** en sélectionnant des joueurs parmi une base de données récupérée. Les principales fonctionnalités sont :

- Création et authentification des utilisateurs via JWT ;
- Gestion CRUD (création, lecture, mise à jour, suppression) des joueurs ;
- Gestion des équipes : chaque utilisateur peut composer une équipe en respectant un budget défini ;
- Routes d'API sécurisées par un système de rôles (utilisateur simple et administrateur) ;
- Seed automatique de la base de données avec un administrateur et des joueurs pré‑définis ;
- Dockerisation de l'ensemble de l'application avec un service API et un service base de données ;
- Suite de tests automatisés pour valider les principales opérations ;
- Gestion centralisée des erreurs HTTP.

## 🚀 Lancer le projet

1. **Cloner le dépôt** et se placer dans le dossier :

   ```bash
   git clone <url_du_repo>
   cd Projet_App_FullStack_Data
   ```

2. **Copier le fichier d'exemple d'environnement** et l'adapter si nécessaire :

   ```bash
   cp .env.example .env
   # Modifier les valeurs si besoin (mot de passe Postgres, SECRET_KEY, BUDGET…)
   ```

3. **Construire et lancer les services Docker** :

   ```bash
   docker‑compose up --build
   ```

   Cela démarre deux conteneurs : `web` pour l'API et `db` pour PostgreSQL.  L'API est accessible à l'adresse <http://localhost:8000>/ui, et la documentation interactive (Swagger) est disponible sur <http://localhost:8000/docs>.

4. **Tester l'API** : consultez la documentation Swagger pour essayer les endpoints.  Utilisez le compte admin (`admin@example.com` / `admin123`) ou créez votre propre utilisateur via l'endpoint `/auth/register`.

5. **Exécuter la suite de tests** (optionnel) :

   ```bash
   docker exec -it $(docker ps -qf name=web) pytest -q
   ```

## 🧱 Structure du projet

```
myfantasyleague/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   ├── database.py          # Création de la connexion et session SQLAlchemy
│   ├── models.py            # Définition des modèles (User, Player, Team, association TeamPlayer)
│   ├── schemas.py           # Schémas Pydantic pour validation et sérialisation
│   ├── auth.py              # Fonctions d'authentification et sécurité JWT
│   ├── crud.py              # Fonctions d'accès aux données
│   ├── dependencies.py      # Dépendances communes (récupération de session, current user…)
│   ├── seed.py              # Script de population de la base au démarrage
│   └── routers/
│       ├── auth.py          # Routes d'authentification (login, register)
│       ├── players.py       # Routes CRUD pour les joueurs
│       └── team.py          # Routes de gestion de l'équipe de l'utilisateur
├── tests/
│   ├── test_auth.py         # Tests d'enregistrement et de connexion
│   ├── test_players.py      # Tests de création et lecture de joueurs
│   └── test_team.py         # Tests de gestion d'équipe et respect du budget
├── Dockerfile               # Image de l'application
├── docker-compose.yml       # Composition des services (API + DB)
├── requirements.txt         # Dépendances Python
├── .env.example             # Fichier d'environnement à adapter
└── README.md                # Ce document
```

## 🧠 Choix techniques et difficultés rencontrées

- **FastAPI & SQLAlchemy** : FastAPI offre une syntaxe moderne et asynchrone et permet de générer automatiquement une documentation Swagger.  SQLAlchemy a été utilisé en mode synchrone pour simplifier l'accès à la base PostgreSQL.
- **JWT & passlib** : l'authentification est basée sur des jetons JWT signés.  Les mots de passe sont hachés avec l'algorithme bcrypt via la bibliothèque Passlib.
- **Gestion du budget** : lors de la création ou mise à jour d'une équipe, l'API vérifie que la somme des coûts des joueurs ne dépasse pas le budget défini dans les variables d'environnement (par défaut 100 000 000).  Un code d'erreur `400` est retourné en cas de dépassement.
- **Tests automatisés** : nous avons mis en place des tests unitaires et d'intégration avec Pytest et HTTPX.  Les tests se lancent contre la base de données dans un environnement isolé, ce qui a nécessité l'utilisation d'une session distincte et la réinitialisation des tables.
- **Docker & docker‑compose** : un `Dockerfile` léger (basé sur Python 3.10) permet de construire l'image.  `docker‑compose` orchestre l'API et la base de données.  Une difficulté a été de s'assurer que la base est prête avant d'exécuter la seed ; nous avons utilisé la politique de `depends_on` et un délai dans le script `seed.py`.

## 🛣️ Pistes d'amélioration

- **Gestion avancée des rôles** : différencier plus finement les droits (ex. rôle coach, observateur, admin) ;
- **Validation des postes** : imposer une composition (4 défenseurs, 4 milieux, 2 attaquants…) ;
- **Points fantasy** : calculer automatiquement des points en fonction des performances réelles des joueurs (requiert des données externes) ;
- **Migration Alembic** : utiliser Alembic pour gérer l'évolution du schéma via des migrations ;
- **Interface Web** : proposer un front‑end React ou Vue pour rendre l'expérience utilisateur plus agréable.

Amusez‑vous à créer votre équipe ! 🥅
