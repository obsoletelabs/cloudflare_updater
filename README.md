[![Build](https://github.com/obsoletelabs/cloudflare_updater/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/obsoletelabs/cloudflare_updater/actions/workflows/docker-publish.yml)
# Obsoletelabs Cloudflare Updater

Most of us have dynamicly assigned IP addresses by our ISPs, especially with ipv4, and this can make self hosting services a pain. 
You have a couple of ways around this, using a DDNS provider with a way to automatically update, realising your services are down and updating your ips, or running local only and requiring VPN/Proxy connection in order to use your services.

This is a way around that. Our company renouned programmers have come up with a docker container, that will keep your IP addresses on cloudflare updated. But simultainously, who can be bothered to keep a service up to date with all the subdomains you use, and what about if you use the same domain on multiple different ip addresses?
Well, thats not a problem! This service records your "old IP" and only updates records with this old IP when your ip changes. This means you can use it on multiple services, with no issue.


# Config

This container does not need any ports bound, as it purely sends outgoing traffic, and has no web interface. Environment variables include:

**WHOAMI_URLS:** A list of urls you wish to use to check your IP, cascading if one fails. This will by default append  ```whoami.obsoletelabs.org:12345``` to your list (including no list specified). 

**OVERRIDE_OBSOLETE_WHOAMI:** If you do not wish to have an obsolete whoami as a fallback, set this value to anything besides ```false```. 

**CLOUDFLARE_API_TOKEN:** This is your cloudflare API token, make sure it can read and write in the zones you want it to update. Note, the container cannot operate if you do not set this.

**CHECK_INTERVAL_SECONDS:** This is where you can configure how frequently the service will poll your IP. The more frequent the less downtime you will experience, but the harsher on your system the service will be. We reccomend a time between 60-1800 seconds for your checking interval. It defaults to 600 seconds (10 minutes).

**RETRY_INTERVAL_SECONDS:** This is where you can figure how often the service will retry if all poll sources fail to respond. This defaults to 10s.

**LOG_LEVEL:** This lets you set the logging level of the output. Valid options are debug, info, warning, error, critical. This defaults to info, and we do not recommend changing this.

**INITIAL_IP:** This lets you set a predetermined initial IP address for the system to use. This can be used to verify it changes the records you expect it to alter without having to wait for your ip address to change. This will set itself to your current ip as determined by the WHOAMI URLs if not set.

### Notifications

**DISCORD_WEBHOOK_URL**: This is a discord webhook url that can optionaly be added to send notifications to discord



# Need help?

We dont provide help to our users. We don't really care if you use us or not. We don't profit off you, we don't store logs, mostly because we don't know how to, therefore we cannot, and will not help. 


## well fine here take this compose file figure it out your self

```yaml
services:
  obsoletelabs_cloudflare_updater:
    image: ghcr.io/obsoletelabs/cloudflare_updater:main
    environment:
      # Required:
      - CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}

      # Optional:
      - WHOAMI_URLS=http://whoami.obsoletelabs.org:12345/ # Comma list of whoami urls
      - OVERRIDE_OBSOLETE_WHOAMI=true # Set this to remove obsolete whoami
      - CHECK_INTERVAL_SECONDS=600 # Delay between ip checks
      - RETRY_INTERVAL_SECONDS=10 # Delay between ip check retries
      - LOG_LEVEL=INFO # Container logging level

      # External notification sources:
      - DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890

```