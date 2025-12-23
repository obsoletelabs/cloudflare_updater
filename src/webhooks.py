import requests

def discord(webhookUrl, MessageContent, username="IP notifier"):
    Message = {
    "username" : username,
    "content" : MessageContent
    }

    result = requests.post(webhookUrl, json = Message)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print(f"Payload delivered successfully, code {result.status_code}.")
        return(result.status_code)

