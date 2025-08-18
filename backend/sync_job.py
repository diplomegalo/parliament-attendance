#!/usr/bin/env python3
"""
Job de synchronisation des données parlementaires.
Script simple qui scrape, parse et sauvegarde en DB.
"""

import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup, Tag
from models import Minute
from database import insert_minutes_bulk

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
        if not isinstance(row, Tag):
            continue
        cells = row.find_all("td")
        if len(cells) < 5:
            logging.error("Le nombre de cellule attendue ne correspond pas")
            continue

        try:
            ref_link = cells[0]("a")
            if ref_link is None:
                logging.error("Lien de référence introuvable")
                continue
            ref = ref_link.text.strip()
            
            # cell_1: Tag = cells[1]
            # session_element = cell_1.find("i")
            # if session_element is None:
                # logging.error("Élément de session introuvable")
                # continue
            # session = session_element.text.strip()
            
            # cell_3: Tag = cells[3]
            # links = cell_3.find_all("a")
            # if len(links) < 3:
                # logging.error("Le nombre de liens attendus ne correspond pas")
                # continue
            # url = links[2]['href']
            
            # cell_2: Tag = cells[2]
            # date_str = cell_2.text.strip()
            # session_date = parse_french_date(date_str)
            
            # cell_4: Tag = cells[4]
            # i_tag = cell_4.find("i")
            # is_temporary = (
                # True if (i_tag is not None and i_tag.text.strip() == "version provisoire")
                # else False
            # )

            # text_integral = fetch_text_integral_from_url(BASE_URL + url)

            # # Création de l'objet Minute
            # minute = Minute(
                # ref=ref,
                # date=session_date.isoformat(),
                # session=session,
                # url=url,
                # is_temporary=is_temporary,
                # text_integral=text_integral
            # )

            # minutes.append(minute)
            # logging.debug(f"Minute récupérée: {minute}")

        except Exception as e:
            logging.warning(f"Erreur lors du parsing d'une ligne: {e}")
            continue

    logging.info(f"✅ {len(minutes)} comptes-rendus récupérés")
    return minutes


def main():
    """Point d'entrée principal."""
    logging.info("🚀 Démarrage du job de synchronisation")

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
