import logging
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loader import dp

from tgbot.filters.approved_user import IsApprovedUserFilter
from tgbot.infrastructure.gmail_service import gmail_service

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsApprovedUserFilter())
dp.include_router(router)


@router.message(Command("emails"))
async def emails_command(message: Message, user_db_id: int, command: CommandObject):
    """
    Handler for /emails command.
    Checks user emails using query or falls back to 'is:unread'.
    """
    query = "is:unread"
    if command.args:
        query = command.args.strip()

    checking_msg = await message.answer("🔄 Checking your emails...")

    try:
        response = await gmail_service.get_emails(user_id=user_db_id, query=query)
        try:
            await checking_msg.delete()
        except Exception as e:
            logger.warning("Failed to delete checking message: %s", e)
        await message.answer(response)
    except Exception as e:
        logger.error("Failed to fetch emails for user %s: %s", user_db_id, e, exc_info=True)
        try:
            await checking_msg.delete()
        except Exception as del_err:
            logger.warning("Failed to delete checking message during error cleanup: %s", del_err)
        await message.answer("❌ Failed to fetch emails. Please try again later.")
