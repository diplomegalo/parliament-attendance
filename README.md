# Parliament Attendance

> 🎵 A vibe coding project - built through intuition, iteration, and practical experimentation.

Un système complet pour analyser la présence réelle des ministres belges aux séances parlementaires. Backend Python avec architecture propre, frontend SSG à venir.

## Structure du Projet

Architecture Clean avec séparation Domain/Application/Infrastructure :

```
parliament-attendance/
├── .github/
│   └── AGENT.md           # Instructions pour agents IA
├── backend/
│   ├── domain/            # Entités métier pures
│   │   ├── entities.py    # SessionReference, ParliamentaryMinute
│   │   └── repositories.py # Interfaces (ports)
│   ├── application/
│   │   └── use_cases.py   # Cas d'usage métier
│   ├── infrastructure/    # Implémentations (adapters)
│   │   ├── web_scraper.py
│   │   ├── database_repository.py
│   │   ├── local_file_storage.py
│   │   └── azure_blob_storage.py
│   ├── tests/             # Tests par couche
│   ├── sync_job.py        # Point d'entrée (injection de dépendances)
│   └── requirements.txt
├── db/
│   └── schema.sql         # Schéma PostgreSQL
├── data/                  # Stockage local (gitignored)
└── README.md
```

## Installation

### Dev Container (Recommended)
This project uses a dev container for consistent development environment. Open in VS Code and select "Reopen in Container" when prompted.

### Backend (Python)

#### With Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
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
```bash
# Database
DB_HOST=localhost
DB_NAME=parliament_attendance
DB_USER=postgres
DB_PASSWORD=password
DB_PORT=5432

# Content Storage ('local' or 'azure')
CONTENT_STORAGE=local

# Azure Blob Storage (si CONTENT_STORAGE=azure)
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_NAME=parliamentary-minutes
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
pytest tests/
```

### Frontend - Mode développement
```bash
cd frontend
npm run dev
```
_(Frontend SSG à implémenter)_

## Fonctionnalités

### Backend (Implémenté)
- **Architecture Clean** : Séparation Domain/Application/Infrastructure
- **Scraping web** : Récupère automatiquement les comptes rendus du Parlement belge (Législature 56)
- **Stockage flexible** : Abstraction pour filesystem local (dev) ou Azure Blob Storage (prod)
- **Base de données** : PostgreSQL pour les métadonnées, contenu HTML séparé
- **Tests complets** : Tests unitaires (domain), tests d'intégration (infrastructure), mocks (use cases)
- **Idempotence** : Gestion des versions provisoires vs définitives

### Frontend (À venir)
- **SSG** : Site statique généré mensuellement (Astro, Next.js SSG, ou Hugo)
- **KPI Ministers** : Taux de présence, votes par ministre
- **Détails des votes** : Consultation des votes par séance

## Architecture

Le projet suit les principes de Clean Architecture et DDD tout en restant simple :
- **Domain-Driven Design** : Entités métier, value objects, interfaces de repositories
- **Clean Architecture** : Dépendances vers l'intérieur (domain ← application ← infrastructure)
- **Séparation des préoccupations** : Infrastructure déléguée aux outils externes
- **Abstraction du stockage** : Changement facile entre local et cloud
- **TDD** : Tests avant implémentation pour la logique métier
- **Principe de simplicité** : Code applicatif purement fonctionnel/métier

### Couches
1. **Domain** : Logique métier pure, aucune dépendance externe
2. **Application** : Cas d'usage orchestrant les règles métier
3. **Infrastructure** : Adaptateurs pour base de données, web scraping, stockage

Consulter `.github/AGENT.md` pour les détails d'implémentation et décisions architecturales.

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour les détails.
