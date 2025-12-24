"""A library for checking your current ip address using whoami"""

import logging

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def get_ip(whoami_urls: list[str]) -> str | None:
    """takes a list of urls to whoami websites and uses them to find the current ip address"""
    firsttry = True

    for url in whoami_urls:  # Attempts to use each url fails over to the next one
        try:
            if firsttry:
                firsttry = False
                logger.info("Checking IP via %s", url)
            else:
                logger.warning("Failover: Checking IP via %s", url)
            result = requests.get(url, timeout=3)
            result.raise_for_status()
            text = result.text.strip()  # clean up the text

            for line in text.split("\n"):
                if "RemoteAddr" in str(line):
                    line = line.strip("RemoteAddr: ")
                    ip = line.split(":")[0]

                    logger.debug(ip)
            break

        except RequestException:
            continue  # failover to the next url
    if ip:
        return ip
    else:
        logger.warning("Failed to get IP from all whoami urls")
        return None
