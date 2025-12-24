"""A library that uses cloudflare's api to find replace all of the ip addresses"""
import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.cloudflare.com/client/v4"

def cloudflare(api_token: str, old_ip: str, new_ip: str):
    """
    Replaces all DNS A records pointing to `old_ip` with `new_ip` across all Cloudflare zones.

    Args:
        api_token (str): Cloudflare API Token with DNS edit permissions.
        old_ip (str): The IP address to search for.
        new_ip (str): The new IP address to replace with.
    """
    if (new_ip == "0.0.0.0") or (new_ip is None):
        raise ValueError("CRITICAL ATTEMPTED TO SET DOMAINS TO 0.0.0.0")# just incase

    logger.info("Starting Cloudflare DNS update process...")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    def get_all_zones():
        zones = []
        page = 1
        while True:
            resp = requests.get(f"{BASE_URL}/zones", headers=headers, params={"page": page, "per_page": 50}, timeout=3)
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

    def get_dns_records(zone_id: str):
        records = []
        page = 1
        while True:
            resp = requests.get(
                f"{BASE_URL}/zones/{zone_id}/dns_records",
                headers=headers,
                params={"page": page, "per_page": 100, "type": "A"},
                timeout=3
            )
            if resp.status_code == 403:
                logger.warning("403 Forbidden: No permission for zone %s, skipping...", zone_id)
                break
            resp.raise_for_status()
            data = resp.json()
            records.extend(data["result"])
            if page >= data["result_info"]["total_pages"]:
                break
            page += 1
        return records

    def update_dns_record(zone_id: str, record_id: str, name: str, ttl: int, proxied: bool):
        payload = {
            "type": "A",
            "name": name.strip(),
            "content": new_ip,
            "ttl": ttl if ttl >= 120 else 1,  # fallback to automatic if too low
            "proxied": proxied  # ensure it's a proper boolean
        }
        try:
            resp = requests.put(
                f"{BASE_URL}/zones/{zone_id}/dns_records/{record_id}",
                headers=headers,
                json=payload,
                timeout=3
            )
            if resp.status_code == 403:
                logger.warning("403 Forbidden: Cannot update record %s in zone %s, skipping...", name, zone_id)
                return
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error updating record %s: %s, payload: %s, response: {getattr(resp, 'text', None)}", name, str(e), payload)


    zones = get_all_zones()
    logger.info("Found %i zones.", len(zones))

    for zone in zones:
        zone_id = zone["id"]
        zone_name = zone["name"]
        records = get_dns_records(zone_id)

        for record in records:
            if record["content"] == old_ip:
                logger.info(f"[%s] Updating {record['name']} (%s --> %s)", zone_name, old_ip, new_ip)
                update_dns_record(zone_id, record["id"], record["name"], record["ttl"], bool(record["proxied"]))

    logger.info("Update complete.")
