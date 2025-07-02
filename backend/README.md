# Backend - Parliament Attendance

Job Python simple pour parser les comptes rendus parlementaires et les insérer dans PostgreSQL.

## Structure

```
backend/
├── sync_job.py         # Script principal (scraping → parsing → insertion)
├── models.py           # Modèle de données (classe Minute)
├── database.py         # Connexion et insertion PostgreSQL
├── test_simple.py      # Tests unitaires simples
├── requirements.txt    # Dépendances Python
└── README.md          # Ce fichier
```

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

Variables d'environnement (dans `.env` à la racine du projet) :
```
DB_HOST=localhost
DB_NAME=parliament_attendance
DB_USER=postgres
DB_PASSWORD=password
DB_PORT=5432
```

## Utilisation

### Lancer le job de synchronisation
```bash
python sync_job.py
```

### Lancer les tests
```bash
python test_simple.py
```

## Fonctionnalités

- **Scraping web** : Parse automatiquement les comptes rendus parlementaires
- **Parser de dates** : Utilise `python-dateutil` pour un parsing robuste des dates
- **Base de données** : Insertion automatique en PostgreSQL avec gestion des doublons
- **Tests simples** : Validation des composants critiques
