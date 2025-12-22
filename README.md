# Obsoletelabs Cloudflare Updater

Most of us have dynamicly assigned IP addresses by our ISPs, especially with ipv4, and this can make self hosting services a pain. 
You have a couple of ways around this, using a DDNS provider with a way to automatically update, realising your services are down and updating your ips, or running local only and requiring VPN/Proxy connection in order to use your services.

This is a way around that. Our company renouned programmers have come up with a docker container, that will keep your IP addresses on cloudflare updated. But simultainously, who can be bothered to keep a service up to date with all the subdomains you use, and what about if you use the same domain on multiple different ip addresses?
Well, thats not a problem! This service records your "old IP" and only updates records with this old IP when your ip changes. This means you can use it on multiple services, with no issue.


# Config

This container does not need any ports bound, as it purely sends outgoing traffic, and has no web interface. Environment variables include:

WHOAMI_URLS: A list of urls you wish to use to check your IP, cascading if one fails. This will default to ```whoami.obsoletelabs.org:12345```.

API_TOKEN: This is your cloudflare API token, make sure it can read and write in the zones you want it to update.

INTERVAL_SECONDS: This is where you can configure how frequently the service will poll your IP. The more frequent the less downtime you will experience, but the harsher on your system the service will be. We reccomend a time between 60-1800 seconds for your checking interval. It defaults to 1800 seconds (30 minutes).


# Need help?

We dont provide help to our users. We don't really care if you use us or not. We don't profit off you, we don't store logs, mostly because we don't know how to, therefore we cannot, and will not help. 
