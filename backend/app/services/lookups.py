from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError
from app.models.entities import Asset, Inspection, User


async def get_asset(db: AsyncSession, organization_id: str, asset_id: str) -> Asset:
    stmt = (
        select(Asset)
        .options(selectinload(Asset.asset_type), selectinload(Asset.location))
        .where(Asset.id == asset_id, Asset.organization_id == organization_id)
    )
    asset = (await db.execute(stmt)).scalar_one_or_none()
    if asset is None:
        raise NotFoundError("Asset", asset_id)
    return asset


async def get_inspection(db: AsyncSession, organization_id: str, inspection_id: str) -> Inspection:
    stmt = (
        select(Inspection)
        .options(
            selectinload(Inspection.observations),
            selectinload(Inspection.measurements),
            selectinload(Inspection.media),
            selectinload(Inspection.risk_assessment),
            selectinload(Inspection.ai_analysis),
            selectinload(Inspection.asset).selectinload(Asset.asset_type),
            selectinload(Inspection.asset).selectinload(Asset.location),
            selectinload(Inspection.inspector),
        )
        .where(Inspection.id == inspection_id, Inspection.organization_id == organization_id)
    )
    inspection = (await db.execute(stmt)).scalar_one_or_none()
    if inspection is None:
        raise NotFoundError("Inspection", inspection_id)
    return inspection


async def get_user(db: AsyncSession, organization_id: str, user_id: str) -> User:
    stmt = select(User).where(User.id == user_id, User.organization_id == organization_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None:
        raise NotFoundError("User", user_id)
    return user
