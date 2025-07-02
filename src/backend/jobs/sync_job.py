# sync_job.py

import requests
import logging
import jobs

jobs.setup_logging()

# Constants
WEB_SITE_URL = "https://www.lachambre.be/kvvcr/showpage.cfm?section=/cricra&language=fr&cfm=dcricra.cfm?type=plen&cricra=cri&count=all"


def syncData():
    logging.info(f"Starting data synchronization from {WEB_SITE_URL}...")
    response = requests.get(WEB_SITE_URL)

    if response.status_code != 200:
        errorMessage = (
            f"Failed to fetch data from {WEB_SITE_URL}. "
            f"Status code:{response.status_code}"
        )
        logging.error(errorMessage)
        raise Exception(errorMessage)

    message = response.text
    logging.info(
        "Data fetched successfully. Length of data: "
        f"{len(message)} characters."
    )


if __name__ == "__main__":
    try:
        syncData()
    except Exception as e:
        logging.exception(f"An error occurred during synchronization: {e}")
        exit(1)
