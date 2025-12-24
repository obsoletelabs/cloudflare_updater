"""A library for sending notifications via diffrent webhooks"""

import requests

def discord(webhook_url, message_content, username="IP notifier"):
    """Discord webhook sender"""
    message = {
    "username" : username,
    "content" : message_content
    }

    result = requests.post(webhook_url, json = message, timeout=3)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print(f"Payload delivered successfully, code {result.status_code}.")
        return

# i dont know why you wanted this but its here now
def generic(webhook_url, message_content):
    """Webhook sender"""
    message = {
    "content" : message_content
    }

    result = requests.post(webhook_url, json = message, timeout=3)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print(f"Payload delivered successfully, code {result.status_code}.")
        return
