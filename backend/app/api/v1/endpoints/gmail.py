from fastapi import APIRouter, HTTPException, Query, status
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from app.api.deps import GmailServiceDep, SessionDep, TargetUserId
from app.schemas.gmail import EmailMessage, EmailMessageList

router = APIRouter()


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
    except ValueError as e:
        error_msg = str(e).lower()
        if "not authorized" in error_msg or "no refresh token" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RefreshError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google access token expired/revoked. Please re-authorize.",
        ) from e
    except HttpError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google API error: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch emails: {str(e)}",
        ) from e


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
    except ValueError as e:
        error_msg = str(e).lower()
        if "not authorized" in error_msg or "no refresh token" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RefreshError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google access token expired/revoked. Please re-authorize.",
        ) from e
    except HttpError as e:
        if e.resp.status == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found.",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google API error: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch email: {str(e)}",
        ) from e
