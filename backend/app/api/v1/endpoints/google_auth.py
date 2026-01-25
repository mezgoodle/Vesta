"""Google OAuth2 authentication endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import SessionDep
from app.services.google_auth import google_auth_service

router = APIRouter()

current_dir = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(current_dir / "templates"))


@router.get("/login")
async def google_login(
    user_id: int = Query(..., description="User ID requesting authorization"),
) -> dict[str, str]:
    """
    Generate Google OAuth2 authorization URL.

    This endpoint is called by the bot to get an authorization URL for a user.
    The user will visit this URL to authorize the application.

    Args:
        user_id: The ID of the user requesting authorization

    Returns:
        Dictionary with authorization URL

    Raises:
        HTTPException: 500 if OAuth credentials are not configured
    """
    try:
        authorization_url = google_auth_service.get_authorization_url(user_id)
        return {
            "authorization_url": authorization_url,
            "message": "Please visit the URL to authorize access to your Google Calendar",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/callback")
async def google_callback(
    request: Request,
    db: SessionDep,
    code: str | None = Query(None, description="Authorization code from Google"),
    state: str | None = Query(None, description="State parameter containing user_id"),
    error: str | None = Query(None, description="Error from Google OAuth"),
) -> HTMLResponse:
    """
    Handle OAuth2 callback from Google.

    This endpoint receives the authorization code from Google after the user
    authorizes the application. It exchanges the code for tokens and saves
    the refresh token to the database.

    Args:
        db: Database session
        code: Authorization code from Google
        state: State parameter (contains user_id)
        error: Optional error parameter if user denied access

    Returns:
        HTML response indicating success or failure

    Raises:
        HTTPException: 400 if user denied access or invalid parameters
        HTTPException: 500 if token exchange or database operation fails
    """
    # Check if user denied access
    if error:
        return templates.TemplateResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            request=request,
            name="error.html",
            context={"request": request},
        )

    # Validate required parameters
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameters: code and state",
        )

    # Exchange code for tokens and save to database
    try:
        result = await google_auth_service.exchange_code_for_token(code, state, db)

        return templates.TemplateResponse(
            request=request,
            name="success.html",
            context={"email": result.get("email", "N/A")},
        )

    except ValueError as e:
        # Invalid state, user not found, or missing refresh token
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        # Token exchange or database error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete authentication: {str(e)}",
        ) from e
