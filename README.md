# Projet App Fantasy League 

## Description

Ce projet a pour objectif d'analyser les statistiques des joueurs de football dans **FIFA 22**, un jeu de simulation de football. En utilisant les données complètes des joueurs disponibles dans FIFA 22, nous explorons des aspects tels que les performances, les nationalités, les clubs, et d'autres caractéristiques des joueurs.


### Objectifs du projet

L’objectif principal est de déterminer les pays ayant les joueurs actuels et futurs possédant les meilleurs notes générales de FIFA 22 à travers un dashboard interactif. Les utilisateurs peuvent explorer différentes statistiques et effectuer des comparaisons entre les joueurs, les clubs et les pays. 

## Table des Matières

- [User Guide](#user-guide)
- [Data](#data)
- [Developer Guide](#developer-guide)
- [Rapport d'analyse](#rapport-danalyse)
- [Copyright](#copyright)

## User Guide

### Prérequis

- **Python 3.7** ou supérieur
- **pip** (gestionnaire de packages Python)

### Installation

1. **Cloner le Répertoire**

   ```bash
   git clone https://git.esiee.fr/dejonghh/projetpythondsia.git
   cd projetpythondsia

2. **Installer les Dépendances**

   ```bash
   pip install -r requirements.txt

3. **Configurer l'API Kaglle**
   Avant d'exécuter le script `get_data.py`, suivez les étapes suivantes pour configurer l'API Kaggle :

3.1. **Créer un compte Kaggle**

   - Rendez-vous sur [Kaggle](https://www.kaggle.com/) et créez un compte.

3.2. **Installer l'API Kaggle**

   - Exécutez la commande suivante pour installer l'API :

     ```bash
     pip install kaggle
     ```

3.3. **Configurer l'authentification**

   - Connectez-vous à Kaggle et allez dans **"My Account"**.
   - Sous **"API"**, cliquez sur **"Create New API Token"** pour télécharger un fichier `kaggle.json`.
   - Placez ce fichier dans le répertoire :
     - **Sous Windows** : `C:\Users\VotreNomUtilisateur\.kaggle\kaggle.json`
     - **Sous Linux/MacOS** : `~/.kaggle/kaggle.json`
   - **Remarque** : Créez le dossier `.kaggle` s'il n'existe pas.

4. **Lancer l'Application**

   - Pour lancer l'application, utilisez la commande : 

     ```bash
     python main.py
     ```

5. **Accéder à l'Application**

   - Une fois l'application démarrée, ouvrez votre navigateur et allez à l'adresse suivante :
      http://localhost:8050/

6. **Utilisation**
   
   Après avoir installé les dépendances et téléchargé les données, vous pouvez maintenant explorer les différentes fonctionnalités du dashboard Club 22.

      - **Navigation** : Utilisez la barre de navigation pour accéder aux différentes pages de l'application : The Club 22, Histogrammes, Carte Interactive des Joueurs et About.
      - **Interactivité** : Cliquez sur les histogrammes ou la carte pour savoir la liste des joueurs correspondant aux critères soumis.
      -  ** Filtres** : Utilisez les filtres proposées pour spécifier les recherches comme la position du joueurs, sa nationalité ou encore son club.
---
## Data

Les données des joueurs proviennent du dataset **"FIFA 22 Complete Player Dataset"** disponible sur Kaggle. Ce jeu de données contient des informations détaillées sur les joueurs de football, notamment :

- **Caractéristiques des joueurs** : Âge, taille, poids, pied fort, position principale, et divers attributs de performance (vitesse, dribble, défense, etc.).
- **Club et nationalité** : Association des joueurs avec leurs clubs et nationalités respectives.
- **Statistiques de performance** : Attributs spécifiques qui influencent la simulation des matchs dans FIFA, tels que les compétences de passe, de tir, et de défense.
 
 Et nous avons également pris un autre fichier csv qui nous donne les coordonnées géographiques des pays (longitude , latitude), disponible sur le site du gouvernement.
 


### Sources des données

- **Kaggle** : Le dataset principal provient de Kaggle, dans le projet `stefanoleone992/fifa-22-complete-player-dataset`.
- **API CurieXplore** : Une base de données complémentaire fournit les coordonnées géographiques des pays, permettant de visualiser les nationalités des joueurs de manière géolocalisée.



---
## Developer Guide

### Architecture du Code

Le projet est structuré selon une architecture modulaire en utilisant **Dash Pages** pour la gestion des différentes pages de l'application.

Voici un diagramme de l'architecture du code en utilisant **Mermaid** :

``` mermaid 
graph TB
    A[PROJETPYTHONDSIA]
    A --> B[src]
    A --> C[data]
    A --> D[assets]
    A --> E[README.md]
    A --> F[requirements.txt]
    A --> G[main.py]
    A --> H[.gitignore]
    A --> I[__init__.py]
    A --> J[config.py]
    
    subgraph src
        B --> B1[styles]
        B --> B2[utils]
        B --> B3[components]
        B --> B4[pages]
        
        B1 --> B1a[style.css]
        
        subgraph utils
            B2 --> B2a[get_data.py]
            B2 --> B2b[clean_data.py]
            B2 --> B2c[preprocess_data.py]
        end
        
        subgraph components
            B3 --> B3a[Navbar.py]
            B3 --> B3b[Header.py]
            B3 --> B3c[Footer.py]
        end
        
        subgraph pages
            B4 --> B4a[about.py]
            B4 --> B4b[theclub.py]
            B4 --> B4c[histograms.py]
            B4 --> B4d[players_map.py]
        end
    end
    
    subgraph data
        C --> C1[raw]
        C --> C2[cleaned]
    end
    
    subgraph assets
        D --> D1[image]
    end


   ```
 ### Ajout d'une Nouvelle Page

 Pour ajouter une nouvelle page à l'application il faut :

 1. Créer un Nouveau Fichier dans le Répertoire `pages/`
   
      - Par exemple,` src/pages/new_page.py`
  
 2. Enregistrer la Page avec Dash
   
   - Dans new_pages.py, ajoutez : 
  
  ``` python 
  import dash
  form dash import html

  dash.register_page(__name__, path='/new_page')

  layout= html.Div([
   #mettre le contenu voulu ici
  ])
  ```

 3. Ajouter le Contenu de la Page 
   
   - Utilisez les composants Dash pour construire le contenu de votre page. 


### Ajout d'un Nouveau Graphique

Pour ajouter un nouveau graphique :

1. Importer les Bibliothèques Nécessaires
   ``` python
   import plotly.express as px
   from dash import dcc
   ```
  

2. Créer le graphique 
   ``` python
   fig = px.scatter(data_frame, x='x_column', y='y_column')
   ```

3. Ajouter le Graphique au Layout
   ``` python
   layout = html.Div([
    # Autres composants
    dcc.Graph(figure=fig)
   ])

---
## Rapport d'analyse

### Les Meilleurs Joueurs

- Dominance des Nations Européennes : La majorité des meilleurs joueurs proviennent de pays européens tels que l'**Espagne**, l'**Allemagne**, la **France** et l'**Angleterre**.
  
 - Continuité des Nations d'Amérique du Sud : La seconde majorité se trouve dans les pays d'Amérique du Sud comme l'**Argentine**, le **Brésil** et L'**Uruguay**.
  
- Concentration dans les Grandes Ligues : On peut observer lorsque l'on clique sur un pays de la carte que tous les joueurs sont présent dans les **5 grand Championnats Européens**.

### Le Meilleur Joueur

- Sur FIFA 22 le meilleur joueur est **Lionel Messi**.



### Les Futurs Meilleurs Joueurs

- Dominance des Nations Européennes : Comme pour les meilleurs joueurs, l'Europe a également le plus grand nombre de joueurs avec le plus grand potentiel, avec comme principale pays la **France**, l'**Allemagne** et l'**Angleterre**.
  
- Continuité des Nations d'Amérique du Sud : Le **Brésil** et l'**Argentine** sont les seuls autres pays à avoir des joueurs à très haut potentiel, le **Brésil** est celui qui en a le plus au monde avec 5.

### Le Futur Meilleur Joueur

- Sur FIFA 22 le futur meilleur joueur est **Kylian Mbappé**.


### Conclusion de l'Analyse 

- Grâce à l'utilisation des histogrammes et de la carte interactive, notre analyse met en lumière les dynamiques globales du football virtuel dans **FIFA 22**. Nous avons pu identifier non seulement les nations dominantes en termes de joueurs actuels performants, mais aussi celles qui possèdent un potentiel significatif pour le futur. Ces analyses démontrent que se sont majoritairement les **Nations Européennes** et **d'Amérique Du Sud** qui ont les meilleurs joueurs actuels. On peut également observer que se sont seulement ces pays là qui auront les futurs grand joueurs.

---


## Copyright

Je déclare sur l'honneur que le code fourni a été produit par moi-même, à l'exception des lignes ci-dessous :

- **Lignes empruntées** :

  - **Exemples de la Documentation Dash** : Certaines portions du code, notamment pour la configuration des callbacks et la mise en page avec Dash Bootstrap Components, ont été inspirées de la documentation officielle de Dash ([Documentation Dash](https://dash.plotly.com/)).

  - **Solutions Stack Overflow** : Des solutions spécifiques à des problèmes rencontrés ont été adaptées à partir de réponses trouvées sur Stack Overflow, notamment pour la gestion des interactions avec les graphiques.

  - **Assistance de ChatGPT** : Des corrections, des résolutions d'erreurs et des optimisations de code ont été réalisées avec l'aide de ChatGPT pour améliorer la qualité et la fonctionnalité de l'application.

- **Explication de la Syntaxe Utilisée** :

  - **Callbacks de Dash** : Utilisation du décorateur `@dash.callback` pour mettre à jour les composants en fonction des interactions utilisateur.

  - **Mermaid pour les Diagrammes** : Utilisation de la syntaxe Mermaid pour représenter l'architecture du code sous forme de diagramme.
