import logging
from fastapi import APIRouter, HTTPException, Query, status
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from app.api.deps import GmailServiceDep, SessionDep, TargetUserId
from app.schemas.gmail import EmailMessage, EmailMessageList

logger = logging.getLogger(__name__)
router = APIRouter()


def _translate_gmail_exception(e: Exception, *, message_id: str | None = None) -> None:
    """
    Map GmailService exceptions to HTTPException and raise.
    Logs sensitive internal details instead of leaking them to clients.
    """
    if isinstance(e, ValueError):
        error_msg = str(e).lower()
        if "not authorized" in error_msg or "no refresh token" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e
        if "failed to create credentials" in error_msg or "failed to build" in error_msg:
            logger.error("Gmail client construction failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google API error occurred. Please try again later.",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    if isinstance(e, RefreshError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google access token expired/revoked. Please re-authorize.",
        ) from e
    if isinstance(e, HttpError):
        if e.resp.status == 404 and message_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found.",
            ) from e
        if e.resp.status == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication credentials invalid or expired. Please re-authorize.",
            ) from e
        logger.error("Google Gmail API error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google API error occurred. Please try again later.",
        ) from e
    logger.exception("Unexpected error in Gmail endpoint")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred. Please try again later.",
    ) from e


@router.get("/messages", response_model=EmailMessageList)
async def get_emails(
    db: SessionDep,
    gmail_service: GmailServiceDep,
    user_id: TargetUserId,
    query: str = Query("is:unread", description="Gmail search query"),
    max_results: int = Query(
        5,
        ge=1,
        le=20,
        description="Number of emails to fetch (1-20)",
    ),
) -> EmailMessageList:
    """
    Search and retrieve Gmail messages for a specific user.
    """
    try:
        emails = await gmail_service.get_emails(
            user_id=user_id,
            db=db,
            query=query,
            max_results=max_results,
        )
        return EmailMessageList(emails=emails, count=len(emails))
    except Exception as e:
        _translate_gmail_exception(e)


@router.get("/messages/{message_id}", response_model=EmailMessage)
async def get_email_by_id(
    message_id: str,
    db: SessionDep,
    gmail_service: GmailServiceDep,
    user_id: TargetUserId,
) -> EmailMessage:
    """
    Get a single Gmail message by ID.
    """
    try:
        return await gmail_service.get_email_by_id(
            user_id=user_id,
            db=db,
            message_id=message_id,
        )
    except Exception as e:
        _translate_gmail_exception(e, message_id=message_id)
