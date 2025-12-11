import logging
import sys

from google.cloud import logging as google_logging
from google.cloud.logging.handlers import CloudLoggingHandler
from google.cloud.logging.handlers import setup_logging as setup_google_logging
from google.cloud.logging_v2.handlers.transports import BackgroundThreadTransport

from app.core.config import settings


def setup_logging() -> None:
    """
    Configures logging based on the environment (DEBUG vs Production).

    If DEBUG is True:
        - Sets up standard Python logging to stdout/stderr.

    If DEBUG is False:
        - Initializes Google Cloud Logging client.
        - Sets up CloudLoggingHandler with BackgroundThreadTransport (non-blocking).
        - Attaches the handler to the root logger.
    """
    if settings.DEBUG:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        logger = logging.getLogger("uvicorn")
        logger.info("Logging configured for LOCAL/DEBUG environment.")
    else:
        try:
            client = google_logging.Client()
            handler = CloudLoggingHandler(
                client, name=settings.GCP_LOG_NAME, transport=BackgroundThreadTransport
            )
            setup_google_logging(handler)
            logging.info("Logging configured for GCP/PRODUCTION environment.")

        except Exception as e:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[logging.StreamHandler(sys.stdout)],
            )
            logging.error(f"Failed to initialize Google Cloud Logging: {e}")
            logging.info("Fallback to standard logging.")
