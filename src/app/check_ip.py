import requests
import os

debug = False

try:
    WHOAMI_URLS = os.environ.get("WHOAMI_URLS").split(",")
except:
    WHOAMI_URLS = [
        "http://whoami.obsoletelabs.org:12345/"
    ]

def get_ip():
    for url in WHOAMI_URLS: # Attempts to use each url fails over to the next one
        try:
            result = requests.get(url, timeout=3)
            result.raise_for_status()
            text = result.text.strip() # clean up the text

            for line in text.split("\n"):
                if "RemoteAddr" in str(line):
                    line = line.strip("RemoteAddr: ")
                    ip, *port = line.split(":")

            if debug: print(ip)
            break
        
        except Exception:
            continue # failover to the next url
    if ip:
        return (True, ip)
    else:
        return (False, 0)