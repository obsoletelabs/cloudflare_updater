"""A library that uses Cloudflare's API to find and replace all IP addresses."""

import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.cloudflare.com/client/v4"


def cloudflare(api_token: str, old_ip: str, new_ip: str) -> None:
    """
    Replaces all DNS A records pointing to `old_ip` with `new_ip` across all Cloudflare zones.

    Args:
        api_token (str): Cloudflare API Token with DNS edit permissions.
        old_ip (str): The IP address to search for.
        new_ip (str): The new IP address to replace with.
    """
    if new_ip == "0.0.0.0" or new_ip is None:
        raise ValueError("CRITICAL: Attempted to set domains to 0.0.0.0")

    logger.info("Starting Cloudflare DNS update process...")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    # ------------------------------------------------------------
    # Fetch all zones
    # ------------------------------------------------------------
    def get_all_zones() -> List[Dict[str, Any]]:
        zones: List[Dict[str, Any]] = []
        page = 1

        while True:
            resp = requests.get(
                f"{BASE_URL}/zones",
                headers=headers,
                params={"page": str(page), "per_page": "50"},
                timeout=3,
            )

            if resp.status_code == 403:
                logger.warning("403 Forbidden: You don't have access to some zones, skipping...")
                break

            resp.raise_for_status()
            data = resp.json()

            zones.extend(data["result"])

            if page >= data["result_info"]["total_pages"]:
                break

            page += 1

        logger.info("Fetched %i zones from Cloudflare.", len(zones))
        logger.debug("Zones: %s", zones)
        return zones

    # ------------------------------------------------------------
    # Fetch DNS A records for a zone
    # ------------------------------------------------------------
    def get_dns_records(zone_id: str) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        page = 1

        while True:
            resp = requests.get(
                f"{BASE_URL}/zones/{zone_id}/dns_records",
                headers=headers,
                params={"page": str(page), "per_page": "100", "type": "A"},
                timeout=3,
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

        logger.info("Fetched %i A records for zone %s.", len(records), zone_id)
        logger.debug("Records for zone %s: %s", zone_id, records)
        return records

    # ------------------------------------------------------------
    # Update a DNS record
    # ------------------------------------------------------------
    def update_dns_record(
        zone_id: str,
        record_id: str,
        name: str,
        ttl: int,
        proxied: bool,
    ) -> None:
        payload = {
            "type": "A",
            "name": name.strip(),
            "content": new_ip,
            "ttl": ttl if ttl >= 120 else 1,
            "proxied": proxied,
        }

        try:
            resp = requests.put(
                f"{BASE_URL}/zones/{zone_id}/dns_records/{record_id}",
                headers=headers,
                json=payload,
                timeout=3,
            )

            if resp.status_code == 403:
                logger.warning(
                    "403 Forbidden: Cannot update record %s in zone %s, skipping...",
                    name,
                    zone_id,
                )
                notifyinformation[name] = "403 Forbidden: No permission to update record."
                return
        
            notifyinformation[name] = "Successfully updated."
            resp.raise_for_status()

        except requests.RequestException as e:
            logger.error(
                "Error updating record %s: %s, payload: %s",
                name,
                str(e),
                payload,
            )
            notifyinformation[name] = f"Error updating record: {str(e)}"

    # ------------------------------------------------------------
    # Main update loop
    # ------------------------------------------------------------
    zones = get_all_zones()
    logger.info("Found %i zones.", len(zones))
    notifyinformation = {}

    for zone in zones:
        zone_id = zone["id"]
        zone_name = zone["name"]

        records = get_dns_records(zone_id)

        for record in records:
            if record["content"] == old_ip:
                logger.info(
                    "[%s] Updating %s (%s → %s)",
                    zone_name,
                    record["name"],
                    old_ip,
                    new_ip,
                )

                update_dns_record(
                    zone_id,
                    record["id"],
                    record["name"],
                    record["ttl"],
                    bool(record["proxied"]),
                )

    logger.info("Update complete.")
    logger.debug("Notification information: %s", notifyinformation)
    return notifyinformation
