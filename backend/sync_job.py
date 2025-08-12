#!/usr/bin/env python3
"""
Job de synchronisation des données parlementaires.
Script simple qui scrape, parse et sauvegarde en DB.
"""

import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from backend.init_db import create_database, run_schema
from models import Minute
from database import insert_minutes_bulk, check_database_connection

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialisation de la base de données
logging.info("Initialisation de la base de données...")
create_database()
run_schema()
logging.info("Base de données initialisée avec succès")

BASE_URL = "https://www.lachambre.be"

# URL de la page à scraper
PAGE_URL = (
    BASE_URL + "/kvvcr/showpage.cfm?"
    "section=/cricra&language=fr&cfm=dcricra.cfm?"
    "type=plen&cricra=CRI&count=all&legislat=56"
)


def parse_french_date(date_str):
    jour, mois, annee = date_str.split(" ", 2)
    mois_fr = {
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
        'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11,
        'décembre': 12
    }

    return datetime(int(annee), mois_fr[mois.lower()], int(jour))


def fetch_text_integral_from_url(url):
    logging.debug(f"Récupération du text intégral depuis {url}...")

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Erreur HTTP {response.status_code}")

    result = response.text
    logging.debug(f"Taille du texte du compte rendu intégral : {len(result)}")

    return result


def fetch_minutes_from_web():
    """Récupère et parse les comptes-rendus depuis le web."""
    logging.info("Récupération des données depuis le web...")

    response = requests.get(PAGE_URL)
    if response.status_code != 200:
        raise Exception(f"Erreur HTTP {response.status_code}")

    page = BeautifulSoup(response.text, "html.parser")
    rows = page.select("table#lst tr")

    if not rows:
        logging.error("Aucune donnée trouvée")
        return []

    logging.debug(f"{len(rows)} compte-rendu trouvé(s)")

    minutes = []
    for row in rows:
        cells = row.find_all(["td"])
        if len(cells) < 5:
            logging.error("Le nombre de cellule attendue ne correspond pas")

        try:
            # Extraction des données
            ref = cells[0].find("a", href=True).text.strip()
            session = cells[1].find("i").text.strip()
            url = cells[3].find_all("a")[2]["href"]
            date_plop = parse_french_date(cells[2].text.strip())
            is_temporary = (
                True if (
                    cells[4].find("i").text.strip() == "version provisoire"
                ) else False
            )

            text_integral = fetch_text_integral_from_url(BASE_URL + url)

            # Création de l'objet Minute
            minute = Minute(
                ref=ref,
                date=date_plop.isoformat(),
                session=session,
                url=url,
                is_temporary=is_temporary,
                text_integral=text_integral
            )

            minutes.append(minute)
            logging.debug(f"Minute récupérée: {minute}")

        except Exception as e:
            logging.warning(f"Erreur lors du parsing d'une ligne: {e}")
            continue

    logging.info(f"✅ {len(minutes)} comptes-rendus récupérés")
    return minutes


def main():
    """Point d'entrée principal."""
    logging.info("🚀 Démarrage du job de synchronisation")

    # Vérification de la connexion DB
    if not check_database_connection():
        logging.error("❌ Impossible de se connecter à la base de données")
        exit(1)

    try:
        # Récupération des données
        minutes = fetch_minutes_from_web()
        
        if minutes:
            # Sauvegarde en base
            insert_minutes_bulk(minutes)
            logging.info(f"✅ {len(minutes)} comptes-rendus sauvegardés")
        else:
            logging.info("Aucune donnée à sauvegarder")
            
    except Exception as e:
        logging.error(f"❌ Erreur durant la synchronisation: {e}")
        exit(1)
    
    logging.info("✅ Synchronisation terminée avec succès")


if __name__ == "__main__":
    main()
