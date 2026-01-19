"""Google OAuth2 authentication service."""

from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user


class GoogleAuthService:
    """Service for handling Google OAuth2 authentication flow."""

    # Scopes required for Google Calendar and user info
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    def __init__(self) -> None:
        """Initialize the Google Auth Service."""
        self.client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        }

    def get_authorization_url(self, user_id: int) -> str:
        """
        Generate Google OAuth2 authorization URL.

        Args:
            user_id: The ID of the user requesting authorization

        Returns:
            Authorization URL for the user to visit

        Raises:
            ValueError: If Google OAuth credentials are not configured
        """
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials not configured")

        if not settings.GOOGLE_REDIRECT_URI:
            raise ValueError("Google redirect URI not configured")

        # Create the flow using the client config
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

        # Generate authorization URL with necessary parameters
        # access_type='offline' ensures we get a refresh token
        # prompt='consent' forces the consent screen even if previously approved
        # include_granted_scopes='true' allows incremental authorization
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
            state=str(user_id),  # Pass user_id as state for callback identification
        )

        return authorization_url

    async def exchange_code_for_token(
        self, code: str, state: str, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Exchange authorization code for tokens and save to database.

        Args:
            code: Authorization code from Google
            state: State parameter (contains user_id)
            db: Database session

        Returns:
            Dictionary with success message and user email

        Raises:
            ValueError: If state is invalid, user not found, or refresh token missing
            Exception: If token exchange or database operation fails
        """
        # Validate state parameter (should be user_id)
        try:
            user_id = int(state)
        except (ValueError, TypeError) as e:
            raise ValueError("Invalid state parameter") from e

        # Verify user exists
        user = await crud_user.get(db, id=user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Create flow for token exchange
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

        # Exchange authorization code for tokens
        try:
            flow.fetch_token(code=code)
        except Exception as e:
            raise Exception(f"Failed to fetch token from Google: {str(e)}") from e

        # Get credentials
        credentials: Credentials = flow.credentials

        # Ensure we have a refresh token
        if not credentials.refresh_token:
            raise ValueError(
                "No refresh token received. User may have already authorized this app. "
                "Please revoke access and try again."
            )

        # Get user info to extract email
        from googleapiclient.discovery import build

        try:
            # Build the OAuth2 service
            oauth2_service = build("oauth2", "v2", credentials=credentials)
            user_info = oauth2_service.userinfo().get().execute()
            email = user_info.get("email")
        except Exception as e:
            raise Exception(f"Failed to get user info from Google: {str(e)}") from e

        # Update user with refresh token and email
        update_data = {"google_refresh_token": credentials.refresh_token}
        if email:
            update_data["email"] = email

        await crud_user.update(db, db_obj=user, obj_in=update_data)

        return {
            "message": "Successfully authenticated with Google",
            "email": email,
            "user_id": user_id,
        }


# Singleton instance
google_auth_service = GoogleAuthService()
