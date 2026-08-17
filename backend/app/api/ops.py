from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession, SupervisorUser
from app.models.entities import Asset, AuditLog, Comment, Notification, new_id
from app.schemas import (
    AuditOut,
    CommentCreate,
    CommentOut,
    KPIResponse,
    MapAssetOut,
    NamedCount,
    NotificationOut,
    TimeSeriesPoint,
)
from app.services import analytics as analytics_service
from app.services.common import utcnow

router = APIRouter(tags=["Analytics, Maps & Inbox"])


@router.get("/analytics/kpis", response_model=KPIResponse)
async def kpis(user: CurrentUser, db: DbSession) -> KPIResponse:
    return await analytics_service.kpis(db, user.organization_id)


@router.get("/analytics/inspections-over-time", response_model=list[TimeSeriesPoint])
async def over_time(user: CurrentUser, db: DbSession, days: int = 30) -> list[TimeSeriesPoint]:
    return await analytics_service.inspections_over_time(db, user.organization_id, days)


@router.get("/analytics/risk-distribution", response_model=list[NamedCount])
async def risk_dist(user: CurrentUser, db: DbSession) -> list[NamedCount]:
    return await analytics_service.risk_distribution(db, user.organization_id)


@router.get("/analytics/issues-by-category", response_model=list[NamedCount])
async def issues(user: CurrentUser, db: DbSession) -> list[NamedCount]:
    return await analytics_service.issues_by_category(db, user.organization_id)


@router.get("/analytics/assets-by-risk", response_model=list[NamedCount])
async def assets_risk(user: CurrentUser, db: DbSession) -> list[NamedCount]:
    return await analytics_service.assets_by_risk(db, user.organization_id)


@router.get("/analytics/inspector-productivity", response_model=list[NamedCount])
async def productivity(user: SupervisorUser, db: DbSession) -> list[NamedCount]:
    return await analytics_service.inspector_productivity(db, user.organization_id)


@router.get("/analytics/resolution-time", response_model=list[TimeSeriesPoint])
async def resolution(user: SupervisorUser, db: DbSession) -> list[TimeSeriesPoint]:
    return await analytics_service.resolution_time(db, user.organization_id)


@router.get("/analytics/top-failing-assets", response_model=list[NamedCount])
async def top_failing(user: CurrentUser, db: DbSession) -> list[NamedCount]:
    return await analytics_service.top_failing_assets(db, user.organization_id)


@router.get("/map/assets", response_model=list[MapAssetOut])
async def map_assets(
    user: CurrentUser,
    db: DbSession,
    risk: str | None = None,
    south: float | None = Query(None),
    north: float | None = Query(None),
    west: float | None = Query(None),
    east: float | None = Query(None),
) -> list[MapAssetOut]:
    stmt = (
        select(Asset)
        .options(selectinload(Asset.asset_type))
        .where(
            Asset.organization_id == user.organization_id,
            Asset.latitude.is_not(None),
            Asset.longitude.is_not(None),
        )
    )
    if risk:
        stmt = stmt.where(Asset.current_risk_level == risk)
    if None not in (south, north, west, east):
        stmt = stmt.where(
            Asset.latitude >= south,
            Asset.latitude <= north,
            Asset.longitude >= west,
            Asset.longitude <= east,
        )
    assets = list((await db.execute(stmt)).scalars().all())
    return [
        MapAssetOut(
            id=asset.id,
            code=asset.code,
            name=asset.name,
            latitude=asset.latitude or 0,
            longitude=asset.longitude or 0,
            current_risk_level=asset.current_risk_level,
            current_risk_score=asset.current_risk_score,
            status=asset.status,
            last_inspection_at=asset.last_inspection_at,
            asset_type_name=asset.asset_type.name if asset.asset_type else None,
        )
        for asset in assets
    ]


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(user: CurrentUser, db: DbSession, unread_only: bool = False) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    stmt = stmt.order_by(Notification.created_at.desc()).limit(100)
    return list((await db.execute(stmt)).scalars().all())


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
async def mark_read(notification_id: str, user: CurrentUser, db: DbSession) -> Notification:
    item = await db.get(Notification, notification_id)
    if item is None or item.user_id != user.id:
        from app.exceptions import NotFoundError

        raise NotFoundError("Notification", notification_id)
    item.read_at = utcnow()
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/notifications/read-all")
async def mark_all_read(user: CurrentUser, db: DbSession) -> dict:
    items = list(
        (
            await db.execute(
                select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
            )
        ).scalars().all()
    )
    now = utcnow()
    for item in items:
        item.read_at = now
    await db.commit()
    return {"updated": len(items)}


@router.get("/audit", response_model=list[AuditOut])
async def audit_log(user: SupervisorUser, db: DbSession, entity_id: str | None = None) -> list[AuditLog]:
    stmt = select(AuditLog).where(AuditLog.organization_id == user.organization_id)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(200)
    return list((await db.execute(stmt)).scalars().all())


@router.post("/comments/{entity_type}/{entity_id}", response_model=CommentOut, status_code=201)
async def add_comment(entity_type: str, entity_id: str, payload: CommentCreate, user: CurrentUser, db: DbSession) -> Comment:
    comment = Comment(
        id=new_id(),
        organization_id=user.organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user.id,
        body=payload.body,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@router.get("/comments/{entity_type}/{entity_id}", response_model=list[CommentOut])
async def list_comments(entity_type: str, entity_id: str, user: CurrentUser, db: DbSession) -> list[Comment]:
    stmt = (
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.organization_id == user.organization_id,
            Comment.entity_type == entity_type,
            Comment.entity_id == entity_id,
        )
        .order_by(Comment.created_at.asc())
    )
    return list((await db.execute(stmt)).scalars().all())
