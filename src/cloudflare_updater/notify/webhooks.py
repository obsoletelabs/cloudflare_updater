"""A library for sending notifications via diffrent webhooks"""

import requests


def discord(webhook_url: str, message_content: str, username: str = "IP notifier"):
    """Discord webhook sender"""
    message = {"username": username, "content": message_content}

    result = requests.post(webhook_url, json=message, timeout=3)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        return err
    else:
        return result.status_code


# i dont know why you wanted this but its here now
def generic(webhook_url: str, message_content: str):
    """Webhook sender"""
    message = {"content": message_content}

    result = requests.post(webhook_url, json=message, timeout=3)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        return err
    else:
        return result.status_code
