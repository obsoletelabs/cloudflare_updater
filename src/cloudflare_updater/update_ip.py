import logging
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.cloudflare.com/client/v4"


def cloudflare(api_token: str, old_ip: str, new_ip: str) -> Dict[str, str]:
    """
    Replaces all DNS A records pointing to `old_ip` with `new_ip` across all Cloudflare zones.
    Includes retry logic, rate-limit handling, and exponential backoff.
    """

    if new_ip == "0.0.0.0" or new_ip is None:
        raise ValueError("CRITICAL: Attempted to set domains to 0.0.0.0")

    logger.info("Starting Cloudflare DNS update process...")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    # ------------------------------------------------------------
    # Unified request wrapper with retries + rate limit handling
    # ------------------------------------------------------------
    def cf_request(
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
        timeout: int = 5,
    ) -> Optional[requests.Response]:

        backoff = 1.0

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=timeout,
                )

                # -------------------------
                # Handle rate limits (429)
                # -------------------------
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else backoff
                    logger.warning(
                        "Rate limited (429). Waiting %.2f seconds before retry %d/%d.",
                        wait,
                        attempt,
                        max_retries,
                    )
                    time.sleep(wait)
                    backoff *= 2
                    continue

                # -------------------------
                # Retry on transient 5xx
                # -------------------------
                if 500 <= resp.status_code < 600:
                    logger.warning(
                        "Cloudflare server error %d. Retrying %d/%d after %.2fs.",
                        resp.status_code,
                        attempt,
                        max_retries,
                        backoff,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                # -------------------------
                # 4xx (except 429) are permanent errors
                # -------------------------
                if 400 <= resp.status_code < 500:
                    logger.error(
                        "Permanent client error %d on %s %s. Not retrying.",
                        resp.status_code,
                        method,
                        url,
                    )
                    return resp

                # Success
                return resp

            except requests.RequestException as e:
                logger.warning(
                    "Network error on attempt %d/%d: %s. Retrying after %.2fs.",
                    attempt,
                    max_retries,
                    str(e),
                    backoff,
                )
                time.sleep(backoff)
                backoff *= 2

        logger.error("Max retries exceeded for %s %s", method, url)
        return None

    # ------------------------------------------------------------
    # Fetch all zones
    # ------------------------------------------------------------
    def get_all_zones() -> List[Dict[str, Any]]:
        zones: List[Dict[str, Any]] = []
        page = 1

        while True:
            resp = cf_request(
                "GET",
                f"{BASE_URL}/zones",
                params={"page": str(page), "per_page": "50"},
            )

            if resp is None:
                logger.error("Failed to fetch zones after retries.")
                break

            if resp.status_code == 403:
                logger.warning("403 Forbidden: Cannot access some zones, skipping...")
                break

            resp.raise_for_status()
            data = resp.json()

            zones.extend(data["result"])

            if page >= data["result_info"]["total_pages"]:
                break

            page += 1

        logger.info("Fetched %i zones from Cloudflare.", len(zones))
        return zones

    # ------------------------------------------------------------
    # Fetch DNS A records for a zone
    # ------------------------------------------------------------
    def get_dns_records(zone_id: str) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        page = 1

        while True:
            resp = cf_request(
                "GET",
                f"{BASE_URL}/zones/{zone_id}/dns_records",
                params={"page": str(page), "per_page": "100", "type": "A"},
            )

            if resp is None:
                logger.error("Failed to fetch DNS records for zone %s.", zone_id)
                break

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

        resp = cf_request(
            "PUT",
            f"{BASE_URL}/zones/{zone_id}/dns_records/{record_id}",
            json=payload,
        )

        if resp is None:
            notifyinformation[name] = "Failed after retries."
            return

        if resp.status_code == 403:
            notifyinformation[name] = "403 Forbidden: No permission to update record."
            return

        if not resp.ok:
            notifyinformation[name] = f"Error updating record: HTTP {resp.status_code}"
            return

        notifyinformation[name] = "Successfully updated."

    # ------------------------------------------------------------
    # Main update loop
    # ------------------------------------------------------------
    zones = get_all_zones()
    notifyinformation: Dict[str, str] = {}

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
    return notifyinformation
