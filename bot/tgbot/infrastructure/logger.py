import logging

from google.cloud import logging as google_logging
from google.cloud.logging.handlers import CloudLoggingHandler
from google.cloud.logging.handlers import setup_logging as setup_google_logging
from google.cloud.logging_v2.handlers.transports import BackgroundThreadTransport
from google.oauth2 import service_account

from tgbot.config import config


def setup_logging() -> None:
    """
    Configures logging based on the environment (DEBUG vs Production).

    If DEBUG is True:
        - Sets up standard Python logging to stdout.

    If DEBUG is False:
        - Initializes Google Cloud Logging client.
        - Sets up CloudLoggingHandler with BackgroundThreadTransport (non-blocking).
        - Attaches the handler to the root logger.
    """
    if config.DEBUG:
        # Development / Local logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s :: %(levelname)s :: %(module)s.%(funcName)s :: %(lineno)d :: %(message)s",
            filename="bot.log",
            filemode="w",
        )
        logger = logging.getLogger(__name__)
        logger.info("Logging configured for LOCAL/DEBUG environment.")
    else:
        # Production / GCP logging
        try:
            if not config.GOOGLE_APPLICATION_CREDENTIALS:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is not set")
            client = google_logging.Client(
                credentials=service_account.Credentials.from_service_account_file(
                    config.GOOGLE_APPLICATION_CREDENTIALS
                )
            )

            # Using CloudLoggingHandler with BackgroundThreadTransport
            handler = CloudLoggingHandler(
                client, name=config.GCP_LOG_NAME, transport=BackgroundThreadTransport
            )

            # Attach handler to root logger
            setup_google_logging(handler)

            logging.info("Logging configured for GCP/PRODUCTION environment.")

        except Exception as e:
            # Fallback to standard logging if GCP connection fails
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s :: %(levelname)s :: %(module)s.%(funcName)s :: %(lineno)d :: %(message)s",
                filename="bot.log",
                filemode="w",
            )
            logging.error(f"Failed to initialize Google Cloud Logging: {e}")
            logging.info("Fallback to standard logging.")
