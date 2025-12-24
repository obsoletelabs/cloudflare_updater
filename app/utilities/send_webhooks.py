"""some code to load webhook shit"""
import yaml
import notify.webhooks as webhooks
import logging

CONFIG_PATH = "/config/webhooks.yml"
logger = logging.getLogger(__name__)

#TODO Should not load config every single time this needs to be fixed
def send(msg: str="default"):
    """Send msg to all webhooks configured"""
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    # Discord
    try:
        if config.get("discord", {"enabled":False})["enabled"]:
            for webhook in config["discord"].get("webhooks", []):
                msg_discord = msg

                if webhook.get("bold", False): msg_discord = "**" + msg_discord + "**"
                if webhook.get("prefix_header", 0) > 0: msg_discord = ("#" * webhook["prefix_header"]) + " " + msg_discord
                msg_discord = msg_discord + webhook.get("ping", "")

                webhooks.discord(webhook["url"], msg_discord, username=webhook["username"])
    except Exception:
        logger.warning("[WARNING] Failed to load discord webhooks")
