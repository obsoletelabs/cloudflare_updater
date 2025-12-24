"""A library for checking your current ip address using whoami"""

from sys import stdout

import logging

import requests

logger = logging.getLogger(__name__)

def get_ip(whoami_urls):
    """takes a list of urls to whoami websites and uses them to find the current ip address"""

    for url in whoami_urls: # Attempts to use each url fails over to the next one
        try:
            logger.info("Checking IP via %s", url)
            result = requests.get(url, timeout=3)
            result.raise_for_status()
            text = result.text.strip() # clean up the text

            for line in text.split("\n"):
                if "RemoteAddr" in str(line):
                    line = line.strip("RemoteAddr: ")
                    ip = line.split(":")[0]

                    logger.debug(ip)
            break

        except Exception:
            continue # failover to the next url
    if ip:
        return (True, ip)
    else:
        logger.warning("Failed to get IP from all whoami urls")
        return (False, "0.0.0.0")
