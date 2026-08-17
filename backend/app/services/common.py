from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog, Notification, User, UserRole, new_id
from app.metrics import critical_notifications_total


async def write_audit(
    db: AsyncSession,
    *,
    organization_id: str,
    user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    log = AuditLog(
        id=new_id(),
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
    )
    db.add(log)
    return log


async def notify_users(
    db: AsyncSession,
    *,
    organization_id: str,
    users: list[User],
    notification_type: str,
    title: str,
    body: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> list[Notification]:
    created: list[Notification] = []
    for user in users:
        item = Notification(
            id=new_id(),
            organization_id=organization_id,
            user_id=user.id,
            notification_type=notification_type,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            extra=extra or {},
        )
        db.add(item)
        created.append(item)
    if notification_type == "critical_risk":
        critical_notifications_total.inc()
    return created


def supervisors_filter(users: list[User]) -> list[User]:
    return [user for user in users if user.role in {UserRole.SUPERVISOR.value, UserRole.OPERATIONS_MANAGER.value, UserRole.ADMIN.value}]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
