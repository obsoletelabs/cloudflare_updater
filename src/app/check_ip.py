import requests

debug = False

URLS = [
    "http://whoami.obsoletelabs.org:12345/"
]

def get_ip():
    for url in URLS:
        try:
            r = requests.get(url, timeout=3)
            r.raise_for_status()
            text = r.text.strip() # clean up the text
            for line in text.split("\n"):
                if "RemoteAddr" in str(line):
                    line = line.strip("RemoteAddr: ")
                    ip, *port = line.split(":")
            if debug: print(ip)
            break
        except Exception:
            continue
    if ip:
        return (True, ip)
    else:
        return (False, 0)