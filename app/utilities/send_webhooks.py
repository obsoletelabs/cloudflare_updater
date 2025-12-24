"""some code to load webhook shit"""
import os
import logging
import yaml
import notify.webhooks as webhooks


CONFIG_PATH = "/config/webhooks.yml"
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "discord": {
        "enabled": False,
        "webhooks": [{
            "username": "IP change notifier",
            "url": "URL HERE",
            "prefix_header": 0,
            "bold": False
        }]
    }
}


def load_config():
    """t"""
    # Ensure file exists
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(DEFAULT_CONFIG, f)

    # Load YAML (may be None)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # Merge missing pieces
    merged = DEFAULT_CONFIG.copy()
    merged["discord"].update(config.get("discord", {}))
    return merged


CONFIG = load_config()

def send(msg: str="default"):
    """Send msg to all webhooks configured"""
    # Discord
    #try: not sure if we need this or not
    if CONFIG.get("discord", {"enabled":False})["enabled"]:
        logger.debug("Discord webhooks enabled sending now.")
        for webhook in CONFIG["discord"].get("webhooks", []):
            msg_discord = msg

            if webhook.get("bold", False):
                msg_discord = "**" + msg_discord + "**"
            if webhook.get("prefix_header", 0) > 0:
                msg_discord = ("#" * webhook["prefix_header"]) + " " + msg_discord
            msg_discord = msg_discord + webhook.get("ping", "")

            webhooks.discord(webhook["url"], msg_discord, username=webhook["username"])
    #except Exception as err:
    #    logger.warning("Failed to load discord webhooks")
    #    logger.warning(err)
