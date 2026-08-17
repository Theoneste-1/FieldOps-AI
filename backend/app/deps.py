from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.entities import User, UserRole, UserStatus
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if creds is None:
        raise UnauthorizedError()
    payload = decode_token(creds.credentials, expected_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Malformed token")
    user = await db.get(User, user_id)
    if user is None or user.status != UserStatus.ACTIVE.value:
        raise UnauthorizedError("Account is not active")
    return user


def require_roles(*roles: UserRole):
    allowed = {role.value for role in roles}

    async def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise ForbiddenError()
        return user

    return checker


SupervisorUser = Annotated[
    User,
    Depends(require_roles(UserRole.SUPERVISOR, UserRole.OPERATIONS_MANAGER, UserRole.ADMIN)),
]
AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def users_in_org(db: AsyncSession, organization_id: str, roles: Sequence[str] | None = None) -> list[User]:
    stmt = select(User).where(User.organization_id == organization_id, User.status == UserStatus.ACTIVE.value)
    if roles:
        stmt = stmt.where(User.role.in_(list(roles)))
    return list((await db.execute(stmt)).scalars().all())


def client_ip(x_forwarded_for: Annotated[str | None, Header()] = None) -> str | None:
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return None
