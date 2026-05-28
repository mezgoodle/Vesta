import logging

from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
)

from loader import dp

logger = logging.getLogger(__name__)


@dp.errors()
async def errors_handler(update, exception) -> bool | None:
    if isinstance(exception, TelegramBadRequest):
        err_msg = str(exception).lower()
        if "message is not modified" in err_msg:
            logger.error("Message is not modified")
            return True
        if "can't parse entities" in err_msg:
            logger.error(f"CantParseEntities: {exception} \nUpdate: {update}")
            return True

    #  MUST BE THE LAST CONDITION
    if isinstance(exception, TelegramAPIError):
        logger.error(f"TelegramAPIError: {exception} \nUpdate: {update}")
        return True

    # At least you have tried.
    logger.error(f"Update: {update} \n{exception}")
    return True
