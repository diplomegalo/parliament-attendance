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
│   │   ├── repositories/  # PostgreSQL repositories
│   │   │   ├── minute_repository.py
│   │   │   └── member_repository.py
│   │   ├── storage/       # File/blob storage
│   │   │   ├── local_file_storage.py
│   │   │   └── azure_blob_storage.py
│   │   └── scrapers/      # Web scrapers
│   │       ├── session_scraper.py
│   │       └── member_scraper.py
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

# Legislature (default: 56)
LEGISLATURE=56

# Content Storage ('local' or 'azure')
CONTENT_STORAGE=local

# Azure Blob Storage (si CONTENT_STORAGE=azure)
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_NAME=parliamentary-minutes

# LLM Provider (un des suivants requis pour compute_attendance_job)
OPENAI_API_KEY=sk-proj-xxxxx                    # OpenAI (recommandé)
# AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/  # Azure OpenAI
# AZURE_OPENAI_API_KEY=xxxxx

# Optional: Fuzzy matching threshold (0-100, default: 85)
FUZZY_MATCH_THRESHOLD=85
```

**Note**: Copiez `.env.example` pour commencer :
```bash
cp .env.example .env
```

## Utilisation

### Pipeline Complet

Le système fonctionne en trois étapes :

#### 1. Synchronisation (Scraping)
Récupère les membres et comptes rendus depuis lachambre.be

```bash
cd backend
LEGISLATURE=56 python sync_job.py
```

#### 2. Nettoyage du Texte
Convertit le HTML en texte clair

```bash
cd backend
LEGISLATURE=56 python extract_attendance_job.py
```

#### 3. Extraction IA (Nouveau ✨)
Utilise l'IA pour extraire les présences et votes

```bash
# Configurer votre clé API OpenAI dans .env
echo "OPENAI_API_KEY=sk-proj-xxxxx" >> .env

# Extraire les présences avec IA
cd backend
LEGISLATURE=56 python compute_attendance_job.py

# Pour une minute spécifique
LEGISLATURE=56 MINUTE_REF=0001 python compute_attendance_job.py
```

**Voir [docs/AI_EXTRACTION.md](docs/AI_EXTRACTION.md) pour plus de détails sur l'extraction IA**

### Synchronisation avec vérification prérequis membres

Le job de synchronisation vérifie automatiquement si les membres existent pour la législature avant de traiter les minutes.

**Processus en deux étapes :**
1. **Étape 1 : Vérification/Scraping des membres** (prérequis)
   - Si membres existent → Continue directement
   - Si absents → Scrape automatiquement depuis `lachambre.be`
2. **Étape 2 : Synchronisation des comptes rendus**

```bash
# Législature par défaut (56)
cd backend
python sync_job.py

# Législature personnalisée
LEGISLATURE=57 python sync_job.py
```

### Backend - Lancer les tests
```bash
cd backend
pytest tests/
# ou test d'intégration rapide
python test_integration_flow.py
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
- **Extraction IA** ✨ : Extraction intelligente des présences avec OpenAI/Azure OpenAI
  - **Abstraction LLM** : Support multi-providers (OpenAI, Azure OpenAI, Anthropic, Ollama)
  - **Fuzzy matching** : Correspondance intelligente des noms (RapidFuzz)
  - **Scoring de confiance** : Combine LLM + fuzzy matching pour fiabilité
- **Pipeline en 3 étapes** :
  1. Scraping des comptes rendus HTML
  2. Nettoyage texte (HTML → plain text)
  3. Extraction IA (présences + votes)
- **Vérification prérequis membres** : Vérifie automatiquement l'existence de la liste des membres avant traitement
- **Scraping automatique membres** : Si absents, scrape depuis `lachambre.be` et sauvegarde
- **Multi-législature** : Support pour différentes législatures via variable `LEGISLATURE`
- **Stockage flexible** : Abstraction pour filesystem local (dev) ou Azure Blob Storage (prod)
- **Base de données** : PostgreSQL pour métadonnées (minutes + membres + présences), contenu séparé
- **Tests complets** : Tests unitaires (domain), tests d'intégration (infrastructure), mocks (use cases)
- **Idempotence** : Gestion des versions provisoires vs définitives, safe re-runs
- **Cas d'usage distincts** :
  - `SynchronizeMembersUseCase` : Gestion liste des membres
  - `SynchronizeMinutesUseCase` : Gestion des comptes rendus
  - `ExtractAttendanceUseCase` : Nettoyage texte HTML
  - (À venir) `ComputeAttendanceUseCase` : Extraction IA

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
   - **Entités** : `SessionReference`, `SessionMetadata`, `ParliamentaryMinute`
   - **Interfaces** : `IMemberRepository`, `IMemberScraper`, `IMinuteRepository`, `IContentStorage`
2. **Application** : Cas d'usage orchestrant les règles métier
   - `SynchronizeMembersUseCase` : Vérification/scraping prérequis membres
   - `SynchronizeMinutesUseCase` : Synchronisation des comptes rendus
3. **Infrastructure** : Adaptateurs pour base de données, web scraping, stockage
   - **Repositories** : `PostgresMemberRepository`, `PostgresMinuteRepository`
   - **Scrapers** : `ChamberMemberScraper`, `ParliamentarySessionScraper`
   - **Storage** : `LocalFileSystemStorage`, `AzureBlobStorage`

### Flux d'exécution (sync_job.py)
```
1. Lire LEGISLATURE depuis env (défaut: 56)
2. Étape 1: SynchronizeMembersUseCase
   └─> has_members? → Oui: Skip | Non: Scrape + Save
3. Étape 2: SynchronizeMinutesUseCase(legislature)
   └─> Retrieve → Filter → Get content → Save
```

Consulter `.github/AGENT.md` pour les détails d'implémentation et décisions architecturales.

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour les détails.
