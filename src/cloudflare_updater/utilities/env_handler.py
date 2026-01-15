import logging
import os
from pathlib import Path

from utilities.value_verifier import is_cloudflare_token_valid

logger = logging.getLogger(__name__)


class Env:
    # Required
    CLOUDFLARE_API_TOKEN: str

    # Debugging
    DEBUG: bool = False
    INITIAL_IP: str | None = None

    WHOAMI_URLS: list = []
    OVERWRITE_OBSOLETE_WHOAMI: bool = False

    ENFORCE_DNS_RESOLUTION: bool = True
    TEST_URL_CONNECTIVITY: bool = True
    ENFORE_URL_CONNECTIVITY: bool = False
    ENFORCE_URL_VALIDITY: bool = False

    CHECK_INTERVAL_SECONDS: int = 600
    RETRY_INTERVAL_SECONDS: int = 10

    LOG_LEVEL: str = "INFO"
    MAX_LOG_BYTES: int = 50 * 1000 * 1000  # 50mb
    ENABLE_COLORED_LOGGING: bool = True

    DISABLE_WELCOME_EMAIL: bool = False
    DISABLE_RESTART_EMAIL: bool = False

    NOTIFIER_SMTP_ENABLED: bool = False
    NOTIFIER_SMTP_SERVER: str | None = None
    NOTIFIER_SMTP_USERNAME: str | None = None
    NOTIFIER_SMTP_PASSWORD: str | None = None
    NOTIFIER_SMTP_EMAIL_FROM_ADDRESS: str | None = None
    NITIFIER_SMTP_EMAIL_TO_ADDRESSES: list = []

    SERVICE_NAME: str = "Obsoletelabs Cloudflare Updater"

    # Internal use
    IS_CONFIG_VALID: bool = True

    # Mapping of supported types to casting functions
    CASTERS = {
        bool: lambda v: v.lower() in ("1", "true", "yes", "on"),
        int: int,
        str: str,
        list: lambda v: v.split(","),
        Path: lambda v: Path(v),
        # NEW: Logging level caster
        "loglevel": lambda v: (logging._nameToLevel.get(v.upper()) if v.upper() in logging._nameToLevel else int(v) if v.isdigit() else None),
    }

    def __init__(self):
        self.load()
        self.validate()
        if not self.IS_CONFIG_VALID:
            exit(1)

    def load(self):
        for attr, annotation in self.__annotations__.items():
            raw = os.getenv(attr)

            # Optional if default exists
            if raw is None and attr in self.__class__.__dict__:
                continue

            if raw is None:
                raise EnvironmentError(f"Missing required environment variable: {attr}")

            # Special handling for LOG_LEVEL
            if attr == "LOG_LEVEL":
                level = self.CASTERS["loglevel"](raw)
                if level is None:
                    raise EnvironmentError(f"Invalid LOG_LEVEL: {raw}. Expected DEBUG, INFO, WARNING, ERROR, CRITICAL, or a number.")
                setattr(self, attr, level)
                continue

            # Normal casting
            caster = self.CASTERS.get(annotation, str)

            try:
                value = caster(raw)
            except Exception:
                expected = annotation.__name__
                raise EnvironmentError(f"Invalid environment variable: {attr}={raw} (expected {expected})")

            setattr(self, attr, value)

    def validate(self):
        """Perform semantic validation of loaded config values."""

        result, result_msg = is_cloudflare_token_valid(self.CLOUDFLARE_API_TOKEN)
        if not result:
            self.IS_CONFIG_VALID = False
            logger.error("[ERROR] CLOUDFLARE_API_TOKEN is invalid: %s", result_msg)
