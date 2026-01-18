from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.crud_user import user as crud_user
from app.schemas.token import Token

router = APIRouter()


@router.post("/access-token", response_model=Token)
async def login_access_token(
    db: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    user = await crud_user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
