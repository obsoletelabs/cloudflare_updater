[![Build](https://github.com/obsoletelabs/cloudflare_updater/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/obsoletelabs/cloudflare_updater/actions/workflows/docker-publish.yml)
[![CI](https://github.com/obsoletelabs/cloudflare_updater/actions/workflows/CI.yml/badge.svg)](https://github.com/obsoletelabs/cloudflare_updater/actions/workflows/CI.yml)
# Obsoletelabs Cloudflare Updater

Most of us have dynamically assigned IP addresses by our ISPs, especially with ipv4, and this can make self hosting services a pain. 
You have a couple of ways around this, using a DDNS provider with a way to automatically update, realising your services are down and updating your ips, or running local only and requiring VPN/Proxy connection in order to use your services.

This is a way around that. Our company renouned programmers have come up with a docker container, that will keep your IP addresses on cloudflare updated. But simultainously, who can be bothered to keep a service up to date with all the subdomains you use, and what about if you use the same domain on multiple different ip addresses?
Well, thats not a problem! This service records your "old IP" and only updates records with this old IP when your ip changes. This means you can use it on multiple services, with no issue.

Also, you can use this with DHCP, run the service on a device with DHCP (and only one connection to the router), with a whoami endpoint on your network with a static IP somehow, and boom. Or run enough of these that DHCP cant break every endpoint (ie 12+, but if you have that many why the hell cant you just use static IPs????)


# Config

This container does not need any ports bound, as it purely sends outgoing traffic, and has no web interface. Environment variables include:

## General config

**WHOAMI_URLS:** A list of urls you wish to use to check your IP, cascading if one fails. This will by default append  ```whoami.obsoletelabs.org:12345``` and ```whoami.obsoletelabs.net:12345``` to your list (including no list specified). This list can consist of URLs with or without http:// or https:// added, as it should autovalidate.

**OVERRIDE_OBSOLETE_WHOAMI:** If you do not wish to have an obsolete whoami as a fallback, set this value to anything besides ```false```. 

**ENFORCE_DNS_RESOLUTION:** By default the url checker will ensure DNS resolution of your whoami URLs, if you do not wish for this to occur, set this value to ```false```. 

**TEST_URL_CONNECTIVITY:** By default the URL checker will test connectivity of the URLs (if it can get a "valid" IP back). If ```ENFORCE_URL_CONNECTIVITY``` is not set, this will just produce a warning in the logs.

**ENFORCE_URL_CONNECTIVITY:** By default the URL checker will not enforce a check on the URL connectivity (as in check if it can recieve an IP address before allowing the URL to be used in the main environment). You can set this value to ```true``` to ensure any values are checked before being in service. This will **not** override ```TEST_URL_CONNECTIVITY```.

**ENFORCE_URL_VALIDITY:** By default the URL checker will not enforce the URLs having to give an IP as an expected output. This requires both ```TEST_URL_CONNECTIVITY``` and ```ENFORCE_URL_CONNECTIVITY``` to be set to ```true```. If this is not set you may still get a warning that no IP was found if the URL connects.

**CLOUDFLARE_API_TOKEN:** This is your cloudflare API token, make sure it can read and write in the zones you want it to update. Note, the container cannot operate if you do not set this.

**CHECK_INTERVAL_SECONDS:** This is where you can configure how frequently the service will poll your IP. The more frequent the less downtime you will experience, but the harsher on your system the service will be. We reccomend a time between 60-1800 seconds for your checking interval. It defaults to 600 seconds (10 minutes).

**RETRY_INTERVAL_SECONDS:** This is where you can figure how often the service will retry if all poll sources fail to respond. This defaults to 10s.

**LOG_LEVEL:** This lets you set the logging level of the output. Valid options are debug, info, warning, error, critical. This defaults to info, and we do not recommend changing this.

**INITIAL_IP:** This lets you set a predetermined initial IP address for the system to use. This can be used to verify it changes the records you expect it to alter without having to wait for your ip address to change. This will set itself to your current ip as determined by the WHOAMI URLs if not set.

**SERVICE_NAME:** Pick the name you want email notifications to say they are for. This defaults to ```Obsoletelabs Cloudflare Updater```, but you can change the name for more informational emails.ß

## SMTP Notifications

Below is the environment imports for the SMTP service. If you dont know how to read it, you probably should set it up. Just get the caps things, set them, or leave them empty if they look like they have suitable defaults.

**NOTIFIER_SMTP_ENABLED:** If you wish to use smtp set this to ```true```, however if necessary values aren't set it will disable itself. It will never enable itself.

**NOTIFIER_SMTP_USERNAME:** This is the username you use to login to the SMTP server, it is required.

**NOTIFIER_SMTP_PASSWORD:** This is the password you use to login to your SMTP server, it is also required.

**NOTIFIER_SMTP_SERVER:** This is where you put the smtp server (eg ```mail.obsoletelabs.net```, which it defaults to because this is obsolete first). This is required if you are not using the Obsolete Labs mail server.

**NOTIFIER_SMTP_SECURITY:** This is where you should define what security standard the mail server you are using uses. Valid options are ```starttls```, ```tls```, and none (any value other than starttls, tls, and not set). This will default to starttls if not set.

**NOTIFIER_SMTP_PORT:** This is where you can define the SMTP port your mail server uses. If not set this will use the default for your security method. (starttls-->587, tls-->465, none-->25)

**NOTIFIER_EMAIL_TO_ADDRESSES:** This is where you define who to send emails to, it can be a comma separated list. Eg: ```admin@obsoletelabs.net,admin2@obsoletelabs.net``` 

**NOTIFIER_EMAIL_FROM_ADDRESS:** This is where you can set what the email will claim to be sent from, if not set it will default to your SMTP username. Examples include ```admin@obsoletelabs.net```, ```Obsoletelabs Admin <admin@obsoletelabs.net>```, and ```"Obsoletelabs Superadmin" <admin@obsoletelabs.net>``` If this is not set to a valid address from for your email server, it may get flagged by email providers.

**NOTIIFER_SMTP_REPLYTO_ADDRESS:** This is where you can set an alternate reply to address for the emails sent. If this is not set it will default to your SMTP username.

**NOTIFIER_SMTP_UNSUBSCRIBE_HEADER:** This is where you can set an unsubscribe header for your emails. This will default to ```<mailto:yoursmtpsender>``` (ie the address sending emails). Valid options include any ```<mailto:>```, or a URL, or can be both: ```<mailto:yourSMTPusername>, <https://yourUnsubscribeAddress.com>```

**NOTIFIER_SMTP_PRECEDENCE:** This is how you can define to other mail servers how the message should be treated. Valid options are ```bulk``` (automated system mail), ```list``` (mailing lists), ```junk``` (low priority emails), or ```auto_reply``` (auto-generated email replies). This will default to bulk, however you can change it if needed. 

**NOTIFIER_SMTP_RETRIES:** This is the number of times that the notifier will attempt to submit/loging to your mail server. This is optional and will default to 3.

**NOTIFIER_SMTP_RETRY_DELAY:** This is the delay between SMTP submission attempts, it is optional and will default to 1.5s.

Additionally, the header for ```Message-ID``` is included by default, and the ```Auto-Submitted``` header is not included. These defaults cannot be customised through environment variables at this time.

Although these SMTP settings seem confusing, this is the minimal environment variables for a server running with starttls on the default port:

```yaml
NOTIFIER_SMTP_ENABLED=true
NOTIFIER_SMTP_USERNAME=youremail@youremail.domain
NOTIFIER_SMTP_PASSWORD=YourSecurePassword123
NOTIIFER_SMTP_SERVER=mail.youremail.domain
NOTIFIER_EMAIL_TO_ADDRESSES=youremail@youremail.domain
```




test branch

# Need help?

We dont provide help to our users. We don't really care if you use us or not. We don't profit off you, we don't store logs, mostly because we don't know how to, therefore we cannot, and will not help. 


## well fine here take this compose file figure it out your self

➡️ [`docker-compose.yml`](./examples/docker-compose.yml)