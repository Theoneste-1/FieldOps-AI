from fastapi import APIRouter
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession
from app.engines.sync_engine import apply_push
from app.metrics import sync_failures
from app.models.entities import Asset, Inspection, SyncDevice, WorkOrder, new_id
from app.schemas import InspectionCreate, SyncPullRequest, SyncPushRequest, SyncPushResult
from app.services.common import utcnow
from app.services.inspections import create_inspection, update_inspection
from app.schemas import InspectionUpdate

router = APIRouter(prefix="/sync", tags=["Synchronization"])


@router.post("/push")
async def push(payload: SyncPushRequest, user: CurrentUser, db: DbSession) -> dict:
    results: list[SyncPushResult] = []
    device = await _device(db, user, payload.device_id, payload.platform, payload.app_version)
    device.last_push_at = utcnow()
    for change in payload.changes:
        try:
            result = await _apply_change(db, user, change.entity_type, change.local_id, change.payload, change.version)
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            sync_failures.labels(reason=change.entity_type).inc()
            results.append(SyncPushResult(local_id=change.local_id, status="failed", message=str(exc)))
    device.last_sync_status = "failed" if any(item.status == "failed" for item in results) else "synced"
    await db.commit()
    return {"device_id": payload.device_id, "results": [item.model_dump() for item in results]}


@router.post("/pull")
async def pull(payload: SyncPullRequest, user: CurrentUser, db: DbSession) -> dict:
    device = await _device(db, user, payload.device_id, "android", None)
    since = payload.since
    assets: list[Asset] = []
    inspections: list[Inspection] = []
    work_orders: list[WorkOrder] = []
    if "assets" in payload.entity_types:
        stmt = select(Asset).options(selectinload(Asset.asset_type), selectinload(Asset.location)).where(
            Asset.organization_id == user.organization_id
        )
        if since:
            stmt = stmt.where(Asset.updated_at >= since)
        assets = list((await db.execute(stmt)).scalars().all())
    if "inspections" in payload.entity_types:
        stmt = (
            select(Inspection)
            .options(
                selectinload(Inspection.observations),
                selectinload(Inspection.measurements),
                selectinload(Inspection.risk_assessment),
                selectinload(Inspection.ai_analysis),
                selectinload(Inspection.asset),
            )
            .where(Inspection.organization_id == user.organization_id)
        )
        if user.role == "inspector":
            stmt = stmt.where(or_(Inspection.inspector_id == user.id, Inspection.updated_at >= (since or utcnow())))
        if since:
            stmt = stmt.where(Inspection.updated_at >= since)
        inspections = list((await db.execute(stmt)).scalars().unique().all())
    if "work_orders" in payload.entity_types:
        stmt = select(WorkOrder).options(selectinload(WorkOrder.asset)).where(WorkOrder.organization_id == user.organization_id)
        if since:
            stmt = stmt.where(WorkOrder.updated_at >= since)
        work_orders = list((await db.execute(stmt)).scalars().all())
    device.last_pull_at = utcnow()
    device.last_sync_status = "synced"
    await db.commit()
    from app.schemas import AssetOut, InspectionOut, WorkOrderOut

    return {
        "server_time": utcnow().isoformat(),
        "assets": [AssetOut.model_validate(item).model_dump(mode="json") for item in assets],
        "inspections": [InspectionOut.model_validate(item).model_dump(mode="json") for item in inspections],
        "work_orders": [WorkOrderOut.model_validate(item).model_dump(mode="json") for item in work_orders],
    }


@router.get("/status")
async def status(user: CurrentUser, db: DbSession) -> dict:
    stmt = select(SyncDevice).where(SyncDevice.user_id == user.id)
    devices = list((await db.execute(stmt)).scalars().all())
    return {
        "devices": [
            {
                "device_id": item.device_id,
                "platform": item.platform,
                "last_pull_at": item.last_pull_at,
                "last_push_at": item.last_push_at,
                "last_sync_status": item.last_sync_status,
            }
            for item in devices
        ]
    }


async def _device(db, user, device_id: str, platform: str, app_version: str | None) -> SyncDevice:
    stmt = select(SyncDevice).where(SyncDevice.user_id == user.id, SyncDevice.device_id == device_id)
    device = (await db.execute(stmt)).scalar_one_or_none()
    if device is None:
        device = SyncDevice(
            id=new_id(),
            organization_id=user.organization_id,
            user_id=user.id,
            device_id=device_id,
            platform=platform,
            app_version=app_version,
        )
        db.add(device)
        await db.flush()
    else:
        device.platform = platform
        if app_version:
            device.app_version = app_version
    return device


async def _apply_change(db, user, entity_type: str, local_id: str, payload: dict, version: int) -> SyncPushResult:
    if entity_type == "inspection":
        stmt = select(Inspection).where(
            Inspection.organization_id == user.organization_id,
            or_(Inspection.local_id == local_id, Inspection.id == payload.get("id")),
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        meta = apply_push(local_id, {**payload, "version": version}, {"id": existing.id, "version": existing.version, "updated_at": existing.updated_at} if existing else None)
        if existing is None:
            created = await create_inspection(db, user, InspectionCreate(local_id=local_id, **{k: v for k, v in payload.items() if k in InspectionCreate.model_fields}))
            return SyncPushResult(local_id=local_id, server_id=created.id, status="synced", server_version=created.version, message="created")
        if meta["status"] == "conflict":
            return SyncPushResult(local_id=local_id, server_id=existing.id, status="conflict", server_version=existing.version, message=meta["message"])
        updated = await update_inspection(
            db,
            user,
            existing.id,
            InspectionUpdate(
                notes=payload.get("notes"),
                weather=payload.get("weather"),
                observations=payload.get("observations"),
                measurements=payload.get("measurements"),
            ),
        )
        return SyncPushResult(local_id=local_id, server_id=updated.id, status="synced", server_version=updated.version, message="updated")
    raise ValueError(f"Unsupported entity type '{entity_type}'")
