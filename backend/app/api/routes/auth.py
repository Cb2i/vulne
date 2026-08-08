from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return TokenResponse(
        access_token=token, role=user.role, full_name=user.full_name, email=user.email
    )


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
