"""Code to import environment variables and verify them"""

from typing import Tuple, Optional
import ipaddress
import logging
import socket
from os import environ
from urllib.parse import urlparse

import requests
import tldextract

logger = logging.getLogger(__name__)

def is_ip_address(hostname) -> bool:
    """Checks if it is a valid ip address"""
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def parse_url(url):
    parsed = urlparse(url)
    return parsed.scheme, parsed.hostname, parsed.port


def has_valid_tld(hostname: str) -> bool:
    ext = tldextract.extract(hostname)
    return ext.suffix != ""


def resolves(hostname) -> bool:
    """Checks if the domain can be resolved to a ip address"""
    try:
        socket.gethostbyname(hostname)
        return True
    except (socket.gaierror, OSError):
        return False


def try_connect(url: str) -> Tuple[bool, Optional[str]]:
    try:
        result = requests.get(url, timeout=3)
        result.raise_for_status()
        text = result.text.strip()  # clean up the text
        ip = None

        for line in text.split("\n"):
            if "RemoteAddr" in line:
                line = line.removeprefix("RemoteAddr: ")
                ip = line.split(":")[0].strip()

                logger.debug(ip)
                break
    except Exception as e:
        return False, str(e)
    else:
        if is_ip_address(ip):
            logger.info("Valid IP found in URL response from %s. Connection successful.", url)
            return True, None
        else:
            logger.info("No valid IP found in URL response from %s. Connection successful.", url)
            return True, "Invalid/no IP in URL response."


def test_http_https(assigned_scheme, url_is_ip: bool, hostname: str, port: Optional[int] = None):
    tested_urls = []
    if url_is_ip:
        schemes = ["http"]
    else:
        schemes = ["https", "http"]

    for scheme in schemes:
        url = f"{scheme}://{hostname}"
        if port:
            url += f":{port}"

        tested_urls.append(url)
        ok, info = try_connect(url)
        if ok:
            if assigned_scheme != scheme:
                logger.warning("Connected via %s, to %s, but assigned scheme is %s.", scheme, url, assigned_scheme)
            return True, [url], info
    return False, tested_urls, None


def validate_url(url):
    enforce_dns_resolution = environ.get("ENFORCE_DNS_RESOLUTION", "false").lower() == "true"
    test_connectivity = environ.get("TEST_URL_CONNECTIVITY", "true").lower() == "true"
    enforce_connectivity = environ.get("ENFORCE_URL_CONNECTIVITY", "false").lower() == "true"
    enforce_validity = environ.get("ENFORCE_URL_VALIDITY", "false").lower() == "true"

    result = {
        "valid": True,
        "reason": "Im a teapot (AKA IP address)",
    }
    scheme, hostname, port = parse_url(url)
    url_is_ip = is_ip_address(hostname)

    if not url_is_ip:
        dns_ok = resolves(hostname)
        # 1. Basic syntax check
        if not hostname:
            result = {"valid": False, "reason": "Invalid URL format (No hostname specified)."}

        # 2. TLD check
        elif not has_valid_tld(hostname):
            result = {"valid": False, "reason": "Invalid URL format (Invalid or missing TLD)."}

        # 3. DNS resolution
        elif not dns_ok:
            if enforce_dns_resolution:
                result = {"valid": False, "reason": "Hostname does not resolve via DNS."}
            else:
                logger.warning("Hostname %s does not resolve via DNS. ", hostname)
        else:
            result = {
                "valid": True,
                "reason": "Passed syntax and DNS checks.",
            }

    # 4. Optional: try HTTP/HTTPS
    if test_connectivity and result["valid"]:
        ok, working_url, info = test_http_https(scheme, url_is_ip, hostname, port)

        if not ok and enforce_connectivity:
            result = {"valid": False, "reason": "Could not connect via HTTP/HTTPS"}
        elif not ok:
            logger.warning("Could not connect to %s via HTTP/HTTPS", hostname)
        elif ok and enforce_validity and info is not None:
            result = {"valid": False, "reason": f"Connection successful but URL response invalid: {info}"}
        elif ok and info is not None:
            logger.warning("Connection successful but URL response invalid: %s", info)

        result["connection_urls"] = working_url
    else:
        result["connection_urls"] = []

    # Log and return
    if result["valid"]:
        if len(result["connection_urls"]) == 1:
            logger.info(
                "URL %s validated with connection URL: %s", url, result["connection_urls"][0]
            )  # means either http or https passed, or enforce connectivity is off and the url is an IP.
        elif len(result["connection_urls"]) > 1:
            logger.info(
                "URL %s validated with multiple connection URLs: %s", url, ", ".join(result["connection_urls"])
            )  # means http and https passed as enforce connectivity is off and neither connected

        return result["connection_urls"]

    else:
        logger.error("URL %s validation failed: %s", url, result["reason"])  # Log reason for failure
        return []


def get_cloudflare_api_token():
    """Get API token from environment variable, check if valid"""

    cloudflare_api_token = environ.get("CLOUDFLARE_API_TOKEN", None)
    if cloudflare_api_token:
        r = requests.get(
            "https://api.cloudflare.com/client/v4/user/tokens/verify", timeout=3, headers={"Authorization": f"Bearer {cloudflare_api_token}"}
        ).json()

        if r.get("success") is False:  # check if api key is invalid
            logger.critical("Cloudflare API token is invalid, please double check and try again. Exiting.")
            logger.critical(r.get("errors"))
            return (False, None)
        else:
            logger.info("Cloudflare API token validated.")
            return (True, cloudflare_api_token)
    else:
        logger.critical("CLOUDFLARE_API_TOKEN environment variable not set. Exiting.")
        return (False, None)
    # logger.info("Cloudflare API token validated.") # Moved to inside the if block to actually work....


def get_whoami_urls():
    """Get WHOAMI_URLS from environment variable or use default"""

    whoami_urls = environ.get("WHOAMI_URLS", "").split(",")
    if environ.get("OVERRIDE_OBSOLETE_WHOAMI", "false").lower() == "false":
        whoami_urls.append("http://whoami.obsoletelabs.org:12345/")  # default fallback 1
        whoami_urls.append("http://whoami.obsoletelabs.net:12345/")  # default fallback 2
    else:
        logger.info("Obsolete WHOAMI URLs NOT appended due to OVERRIDE_OBSOLETE_WHOAMI setting.")

    if whoami_urls == [""]:
        logger.critical("WHOAMI_URLS environment variable empty and obsolete fallback disabled. Exiting.")
        return (False, None)

    # Validate whoami_urls
    output_whoami_urls = []
    for url in whoami_urls:
        if url != "":  # Skip empty entries
            if "://" not in url:
                url = "none://" + url  # default to http if no scheme provided
            valid_urls = validate_url(url)
            output_whoami_urls.extend(valid_urls)

    if len(output_whoami_urls) == 0:
        logger.critical("No valid WHOAMI_URLS found after validation. Exiting.")
        return (False, None)

    return (True, output_whoami_urls)
