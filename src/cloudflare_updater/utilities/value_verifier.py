import requests
import ipaddress

def is_cloudflare_token_valid(token: str) -> tuple[bool, str]:
    """
    Validate a Cloudflare API token using the /user/tokens/verify endpoint.

    Args:
        token (str): The Cloudflare API token to validate.

    Returns:
        (bool, str): A tuple where:
            - bool indicates whether the token is valid.
            - str contains a message or error detail.
    """
    url = "https://api.cloudflare.com/client/v4/user/tokens/verify"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as e:
        return False, f"Network error while verifying token: {e}"

    # If Cloudflare returns non-JSON or unexpected structure
    try:
        data = response.json()
    except ValueError:
        return False, "Invalid response from Cloudflare (not JSON)."

    # Cloudflare always includes "success"
    if not data.get("success"):
        # Extract Cloudflare error message if available
        errors = data.get("errors", [])
        if errors:
            return False, f"Cloudflare error: {errors[0].get('message', 'Unknown error')}"
        return False, "Token verification failed."

    # Check token status
    status = data.get("result", {}).get("status")
    if status != "active":
        return False, f"Token is not active (status: {status})."

    return True, "Token is valid and active."

def is_ip_address(hostname) -> bool:
    """Checks if it is a valid ip address"""
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False




