from time import sleep
import os
from pathlib import Path

import update_ip
from check_ip import get_ip 

old_ip = None # initialize old_ip variable

try:
    sleep_time = int(os.environ.get("INTERVAL_SECONDS")) # check interval from environment variable
except:
    sleep_time = 300 # Set default to 5 minutes

# Get API token from environment variable
try:
    API_TOKEN = os.environ.get("API_TOKEN")
except:
    print("API_TOKEN environment variable not set. Exiting.")
    exit(1)

def main():
    # Main loop
    while True:
        sleep(sleep_time)  # wait 5 minutes between checks

        #API_TOKEN = os.environ.get("API_TOKEN")
        #FILE_PATH = Path("/ip.txt") # location to cache ip addresses

        found, ip = get_ip() # grab the current ip address

        try:
            if found and ip != old_ip: # if ip has changed
                new_ip = ip
                print(f"IP change detected: {old_ip} --> {new_ip}")
                update_ip.cloudflare(API_TOKEN, old_ip, new_ip)
                old_ip = ip
                print(f"Updated cached IP to: {new_ip}")
        except:
            print("Error updating IP address.")

    


if __name__ == "__main__": 
    main()