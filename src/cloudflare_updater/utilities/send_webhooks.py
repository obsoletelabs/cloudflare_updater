import logging
import os
from typing import Any, Dict, List

import notify.webhooks as webhooks
import yaml


logger = logging.getLogger(__name__)

CONFIG_PATH = "/config/webhooks.yml"

DEFAULT_CONFIG: Dict[str, Any] = {
    "discord": {
        "enabled": False,
        "webhooks": [
            {
                "username": "IP change notifier",
                "url": "URL HERE",
                "prefix_header": 0,
                "bold": False,
                "ping": "",
            }
        ],
    }
}


def load_config() -> Dict[str, Any]:
    """Load webhook configuration from YAML, creating defaults if missing."""

    # Ensure directory exists
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    # Create file if missing
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(DEFAULT_CONFIG, f)

    # Load YAML safely
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception as err:
        logger.error("Failed to load webhook config, using defaults.")
        logger.error(err)
        return DEFAULT_CONFIG.copy()

    # Deep merge discord config
    merged = DEFAULT_CONFIG.copy()
    merged["discord"] = DEFAULT_CONFIG["discord"].copy()

    user_discord = config.get("discord", {})
    merged["discord"].update(user_discord)

    # Ensure webhooks list exists and is valid
    if not isinstance(merged["discord"].get("webhooks"), list):
        merged["discord"]["webhooks"] = DEFAULT_CONFIG["discord"]["webhooks"]

    return merged


def send(msg: str = "default") -> None:
    """Send a message to all configured webhooks."""

    config = load_config()
    discord_cfg = config.get("discord", {})

    if not discord_cfg.get("enabled", False):
        return

    logger.debug("Discord webhooks enabled, sending now.")

    webhooks_list: List[Dict[str, Any]] = discord_cfg.get("webhooks", [])

    for webhook in webhooks_list:
        try:
            msg_discord = msg

            # Bold formatting
            if webhook.get("bold", False):
                msg_discord = f"**{msg_discord}**"

            # Prefix header (### etc.)
            prefix = webhook.get("prefix_header", 0)
            if isinstance(prefix, int) and prefix > 0:
                msg_discord = f"{'#' * prefix} {msg_discord}"

            # Optional ping
            msg_discord += webhook.get("ping", "")

            # Send webhook
            webhooks.discord(
                webhook["url"],
                msg_discord,
                username=webhook.get("username", "Notifier"),
            )

        except Exception as err:
            logger.warning("Failed to send Discord webhook")
            logger.warning(err)
