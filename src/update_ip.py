import requests

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.cloudflare.com/client/v4"

def cloudflare(api_token, old_ip, new_ip):
    """
    Replaces all DNS A records pointing to `old_ip` with `new_ip` across all Cloudflare zones.

    Args:
        api_token (str): Cloudflare API Token with DNS edit permissions.
        old_ip (str): The IP address to search for.
        new_ip (str): The new IP address to replace with.
    """
    
    logger.info("Starting Cloudflare DNS update process...")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    def get_all_zones():
        zones = []
        page = 1
        while True:
            resp = requests.get(f"{BASE_URL}/zones", headers=headers, params={"page": page, "per_page": 50})
            if resp.status_code == 403:
                logger.warning("403 Forbidden: You don't have access to some zones, skipping...")
                break
            resp.raise_for_status()
            data = resp.json()
            zones.extend(data["result"])
            if page >= data["result_info"]["total_pages"]:
                break
            page += 1
        return zones

    def get_dns_records(zone_id):
        records = []
        page = 1
        while True:
            resp = requests.get(
                f"{BASE_URL}/zones/{zone_id}/dns_records",
                headers=headers,
                params={"page": page, "per_page": 100, "type": "A"}
            )
            if resp.status_code == 403:
                logger.warning(f"403 Forbidden: No permission for zone {zone_id}, skipping...")
                break
            resp.raise_for_status()
            data = resp.json()
            records.extend(data["result"])
            if page >= data["result_info"]["total_pages"]:
                break
            page += 1
        return records

    def update_dns_record(zone_id, record_id, name, ttl, proxied):
        payload = {
            "type": "A",
            "name": name.strip(),
            "content": new_ip,
            "ttl": ttl if ttl >= 120 else 1,  # fallback to automatic if too low
            "proxied": bool(proxied)  # ensure it's a proper boolean
        }
        try:
            resp = requests.put(
                f"{BASE_URL}/zones/{zone_id}/dns_records/{record_id}", 
                headers=headers, 
                json=payload
            )
            if resp.status_code == 403:
                logger.warning(f"403 Forbidden: Cannot update record {name} in zone {zone_id}, skipping...")
                return
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error updating record {name}: {e}, payload: {payload}, response: {getattr(resp, 'text', None)}")


    zones = get_all_zones()
    logger.info(f"Found {len(zones)} zones.")

    for zone in zones:
        zone_id = zone["id"]
        zone_name = zone["name"]
        records = get_dns_records(zone_id)

        for record in records:
            if record["content"] == old_ip:
                logger.info(f"[{zone_name}] Updating {record['name']} ({old_ip} → {new_ip})")
                update_dns_record(zone_id, record["id"], record["name"], record["ttl"], record["proxied"])

    logger.info("Update complete.")