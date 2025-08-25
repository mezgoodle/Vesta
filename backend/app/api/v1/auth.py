from app.core.database import get_session
from app.models.user import UserCreate, UserRead
from app.services.user import UserService
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

router = APIRouter()
user_service = UserService()


@router.post("/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_session)):
    return user_service.create(db, obj_in=user_in)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)
) -> dict[str, str | UserRead]:
    user = user_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Note: In a real application, you would generate a JWT token here
    return {
        "access_token": f"token_for_user_{user.id}",
        "token_type": "bearer",
        "user": user,
    }


@router.post("/logout")
def logout() -> dict[str, str]:
    # Note: In a real application, you would invalidate the token here
    return {"message": "Successfully logged out"}
