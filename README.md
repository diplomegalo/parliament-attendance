# Parliament Attendance

Un système complet pour parser les comptes rendus parlementaires avec un backend Python et un frontend Next.js.

## Structure du Projet

Le projet maintient une séparation claire entre frontend et backend :

```
parliament-attendance/
├── backend/                # Backend Python
│   ├── sync_job.py         # Script principal (scraping → parsing → insertion)
│   ├── models.py           # Modèle de données (classe Minute)
│   ├── database.py         # Connexion et insertion PostgreSQL
│   ├── test_simple.py      # Tests unitaires simples
│   ├── requirements.txt    # Dépendances Python
│   └── README.md          # Documentation backend
├── frontend/              # Frontend Next.js
│   ├── src/               # Code source React/Next.js
│   ├── package.json       # Dépendances Node.js
│   └── [configuration files]
├── schema.sql             # Schéma de base de données
└── README.md             # Ce fichier
```

## Installation

### Backend (Python)
```bash
cd backend
pip install -r requirements.txt
```

### Frontend (Next.js)
```bash
cd frontend
npm install
```

### Base de données
```bash
psql -d votre_base -f schema.sql
```

## Configuration

Variables d'environnement dans `.env` à la racine :
```
DB_HOST=localhost
DB_NAME=parliament_attendance
DB_USER=postgres
DB_PASSWORD=password
DB_PORT=5432
```

## Utilisation

### Backend - Lancer le job de synchronisation
```bash
cd backend
python sync_job.py
```

### Backend - Lancer les tests
```bash
cd backend
python test_simple.py
```

### Frontend - Mode développement
```bash
cd frontend
npm run dev
```

## Fonctionnalités

### Backend
- **Scraping web** : Parse automatiquement les comptes rendus parlementaires
- **Parser de dates** : Utilise `python-dateutil` pour un parsing robuste
- **Base de données** : Insertion automatique en PostgreSQL avec gestion des doublons
- **Tests simples** : Validation des composants critiques

### Frontend
- **Interface web moderne** : Dashboard pour visualiser les données
- **Next.js + TypeScript** : Stack moderne et typée
- **Tailwind CSS** : Styling utilitaire

## Architecture

Le projet évite la sur-ingénierie tout en maintenant une séparation logique :
- **Séparation claire** : Backend et frontend distincts
- **Structure simple** : Pas de packages Python complexes
- **Dépendances minimales** : Seulement les packages essentiels
- **Tests ciblés** : Validation des parties critiques uniquement

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour les détails.
