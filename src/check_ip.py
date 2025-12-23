import sys

import logging

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

debug = False



def get_ip(WHOAMI_URLS):

    for url in WHOAMI_URLS: # Attempts to use each url fails over to the next one
        try:
            logger.info(f"Checking IP via {url}")
            result = requests.get(url, timeout=3)
            result.raise_for_status()
            text = result.text.strip() # clean up the text

            for line in text.split("\n"):
                if "RemoteAddr" in str(line):
                    line = line.strip("RemoteAddr: ")
                    ip, *port = line.split(":")

                    logger.debug(ip)
            break
        
        except Exception:
            continue # failover to the next url
    if ip:
        return (True, ip)
    else:
        return (False, 0)