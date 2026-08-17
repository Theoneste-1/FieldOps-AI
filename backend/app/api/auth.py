from datetime import datetime, timezone

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.config import get_settings
from app.deps import CurrentUser, DbSession
from app.exceptions import UnauthorizedError
from app.models.entities import Organization, User, UserStatus
from app.schemas import LoginRequest, OrganizationOut, RefreshRequest, TokenResponse, UserOut
from app.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.services.common import write_audit

router = APIRouter(prefix="/auth", tags=["Identity"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DbSession, request: Request) -> TokenResponse:
    stmt = select(User).where(User.email == payload.email.lower())
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    if user.status != UserStatus.ACTIVE.value:
        raise UnauthorizedError("Account is not active")
    user.last_login_at = datetime.now(timezone.utc)
    await write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
        new_value={"device_id": payload.device_id},
    )
    await db.commit()
    return _tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenResponse:
    data = decode_token(payload.refresh_token, expected_type="refresh")
    user = await db.get(User, data.get("sub"))
    if user is None or user.status != UserStatus.ACTIVE.value:
        raise UnauthorizedError("Invalid refresh token")
    return _tokens(user)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> User:
    return user


@router.get("/organization", response_model=OrganizationOut)
async def organization(user: CurrentUser, db: DbSession) -> Organization:
    org = await db.get(Organization, user.organization_id)
    return org


def _tokens(user: User) -> TokenResponse:
    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user.id, user.role, user.organization_id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserOut.model_validate(user),
    )
