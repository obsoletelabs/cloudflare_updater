"""A library for checking your current ip address using whoami"""

import logging

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def get_ip(whoami_urls: list[str]) -> tuple[str, str] | None:
    """takes a list of urls to whoami websites and uses them to find the current ip address, and name of the whoami url that provided the ip address, if any"""
    firsttry = True
    ip = None # This should fix the issue of ip being referenced before assignment if all urls fail
    remote_addr = None
    x_forwarded_ip = None

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
            whoami_name = url

            for line in text.split("\n"):
                if "Name" in str(line):
                    line = line.strip("Name: ")
                    whoami_name = line
                    logger.debug(f"whoami URL {url} presented name of {whoami_name}")

                elif "RemoteAddr" in str(line):
                    line = line.strip("RemoteAddr: ")
                    remote_addr = line.split(":")[0]
                    logger.debug(f"whoami URL {url} presented RemoteAddr of {remote_addr}")

                elif "X-Forwarded-For" in str(line):
                    line = line.strip("X-Forwarded-For: ")
                    x_forwarded_ip = line.split(",")[0].strip()
                    logger.debug(f"whoami URL {url} presented X-Forwarded-For of {x_forwarded_ip}")

            if x_forwarded_ip or remote_addr: # I dont think its happening but make sure it doesnt break if the whoami url doesnt present the expected output, but still sends a response
                break

        except RequestException:
            continue  # failover to the next url

    if x_forwarded_ip:
        logger.debug(f"Using X-Forwarded-For IP: {x_forwarded_ip} from {whoami_name}")
        return x_forwarded_ip, whoami_name
    elif remote_addr:
        logger.debug(f"Using RemoteAddr IP: {remote_addr} from {whoami_name}")
        return remote_addr, whoami_name
    #if ip:
    #    return ip
    else:
        logger.warning("Failed to get IP from all whoami urls")
        return None, None
