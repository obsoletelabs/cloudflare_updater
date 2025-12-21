from update_ip import update_ip_on_cloudflare
from time import sleep
from check_ip import get_ip
from pathlib import Path
import os

API_TOKEN = os.environ.get("API_TOKEN")


FILE_PATH = Path("ip.txt")


found, ip = get_ip()

if found:

    if FILE_PATH.exists():
        first_line = FILE_PATH.read_text().splitlines()[0]
    else:
        first_line = None

    if first_line != ip:
        FILE_PATH.write_text(ip)
        print("WARNING ip change detected!!!")
        if first_line != None:
            update_ip_on_cloudflare(API_TOKEN, first_line, ip)
            pass

    print(ip)


while True:
    sleep(30)

