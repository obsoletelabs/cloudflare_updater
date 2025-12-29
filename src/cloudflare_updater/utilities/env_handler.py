import os
from pathlib import Path


class Env:

    DEBUG: bool = False          # optional, default False
    WHOAMI_URLS: list = []       # optional
    OVERWRITE_OBSOLETE_WHOAMI: bool = False
    ENFORCE_DNS_RESOLUTION: bool = True
    TEST_URL_CONNECTIVITY: bool = True
    ENFORE_URL_CONNECTIVITY: bool = False
    ENFORCE_URL_VALIDITY: bool = False #TODO can we confirm the default
    CLOUDFLARE_API_TOKEN: str # REQUIRED
    CHECK_INTERVAL_SECONDS: int = 600
    RETRY_INTERVAL_SECONDS: int = 10
    LOG_LEVEL: str = "INFO" #TODO add logic to handle real log level type
    INITIAL_IP: str | None = None # likely needs fixing
    SERVICE_NAME: str = "Obsoletelabs Cloudflare Updater"




    # Mapping of supported types to casting functions
    CASTERS = {
        bool: lambda v: v.lower() in ("1", "true", "yes", "on"),
        int: int,
        str: str,
        list: lambda v: v.split(","),
        Path: lambda v: Path(v),
    }

    def __init__(self):
        """
        Initialize the Env loader and immediately load all environment variables.
        """
        self.load()

    def load(self):
        """
        Load and validate environment variables based on class annotations.

        Behavior:
        - If a variable is missing but has a class-level default, it is optional.
        - If a variable is missing and has no default, an error is raised.
        - Values are cast according to the annotation type using CASTERS.
        - Invalid values raise a descriptive EnvironmentError.

        Raises:
            EnvironmentError: If a required variable is missing or cannot be cast.
        """
        for attr, annotation in self.__annotations__.items():
            raw = os.getenv(attr)

            # Optional if a default exists on the class
            if raw is None and attr in self.__class__.__dict__:
                continue

            # Required if no default
            if raw is None:
                raise EnvironmentError(f"Missing required environment variable: {attr}")

            caster = self.CASTERS.get(annotation, str)

            try:
                value = caster(raw)
            except Exception:
                expected = annotation.__name__
                raise EnvironmentError(
                    f"Invalid environment variable: {attr}={raw} (expected {expected})"
                )

            setattr(self, attr, value)
