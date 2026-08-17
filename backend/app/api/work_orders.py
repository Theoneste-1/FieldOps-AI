from datetime import timedelta

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession, SupervisorUser
from app.exceptions import InvalidStateError, NotFoundError
from app.metrics import work_orders_created_total
from app.models.entities import (
    NotificationType,
    User,
    WorkOrder,
    WorkOrderStatus,
    new_id,
)
from app.schemas import WorkOrderCreate, WorkOrderOut, WorkOrderUpdate
from app.services.common import notify_users, utcnow, write_audit
from app.services.lookups import get_asset, get_user

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])

TRANSITIONS = {
    WorkOrderStatus.OPEN.value: {WorkOrderStatus.ASSIGNED.value, WorkOrderStatus.CANCELLED.value},
    WorkOrderStatus.ASSIGNED.value: {WorkOrderStatus.IN_PROGRESS.value, WorkOrderStatus.OPEN.value, WorkOrderStatus.CANCELLED.value},
    WorkOrderStatus.IN_PROGRESS.value: {WorkOrderStatus.COMPLETED.value, WorkOrderStatus.ASSIGNED.value},
    WorkOrderStatus.COMPLETED.value: {WorkOrderStatus.VERIFIED.value, WorkOrderStatus.IN_PROGRESS.value},
    WorkOrderStatus.VERIFIED.value: set(),
    WorkOrderStatus.CANCELLED.value: set(),
}


@router.get("", response_model=list[WorkOrderOut])
async def list_work_orders(
    user: CurrentUser,
    db: DbSession,
    status: str | None = None,
    asset_id: str | None = None,
    mine: bool = False,
) -> list[WorkOrder]:
    stmt = (
        select(WorkOrder)
        .options(selectinload(WorkOrder.asset))
        .where(WorkOrder.organization_id == user.organization_id)
    )
    if status:
        stmt = stmt.where(WorkOrder.status == status)
    if asset_id:
        stmt = stmt.where(WorkOrder.asset_id == asset_id)
    if mine or user.role == "inspector":
        stmt = stmt.where(WorkOrder.assigned_to == user.id)
    stmt = stmt.order_by(WorkOrder.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


@router.post("", response_model=WorkOrderOut, status_code=201)
async def create_work_order(payload: WorkOrderCreate, user: SupervisorUser, db: DbSession) -> WorkOrder:
    asset = await get_asset(db, user.organization_id, payload.asset_id)
    order = WorkOrder(
        id=new_id(),
        organization_id=user.organization_id,
        inspection_id=payload.inspection_id,
        asset_id=asset.id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=WorkOrderStatus.ASSIGNED.value if payload.assigned_to else WorkOrderStatus.OPEN.value,
        assigned_to=payload.assigned_to,
        created_by=user.id,
        due_at=payload.due_at or utcnow() + timedelta(days=3),
    )
    db.add(order)
    work_orders_created_total.labels(priority=order.priority).inc()
    if payload.assigned_to:
        assignee = await get_user(db, user.organization_id, payload.assigned_to)
        await notify_users(
            db,
            organization_id=user.organization_id,
            users=[assignee],
            notification_type=NotificationType.WORK_ORDER.value,
            title="Work order assigned",
            body=f"{order.title} was assigned to you for {asset.code}.",
            entity_type="work_order",
            entity_id=order.id,
        )
    await write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="work_order.created",
        entity_type="work_order",
        entity_id=order.id,
        new_value=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/{work_order_id}", response_model=WorkOrderOut)
async def get_work_order(work_order_id: str, user: CurrentUser, db: DbSession) -> WorkOrder:
    order = await db.get(WorkOrder, work_order_id)
    if order is None or order.organization_id != user.organization_id:
        raise NotFoundError("Work order", work_order_id)
    return order


@router.patch("/{work_order_id}", response_model=WorkOrderOut)
async def update_work_order(work_order_id: str, payload: WorkOrderUpdate, user: CurrentUser, db: DbSession) -> WorkOrder:
    order = await db.get(WorkOrder, work_order_id)
    if order is None or order.organization_id != user.organization_id:
        raise NotFoundError("Work order", work_order_id)
    old_status = order.status
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] != order.status:
        allowed = TRANSITIONS.get(order.status, set())
        if data["status"] not in allowed:
            raise InvalidStateError(f"Cannot move work order from {order.status} to {data['status']}")
        if data["status"] == WorkOrderStatus.IN_PROGRESS.value:
            order.started_at = utcnow()
        if data["status"] == WorkOrderStatus.COMPLETED.value:
            order.completed_at = utcnow()
        if data["status"] == WorkOrderStatus.VERIFIED.value:
            if user.role == "inspector":
                raise InvalidStateError("Inspectors cannot verify work orders")
            order.verified_at = utcnow()
            order.verified_by = user.id
    if "assigned_to" in data and data["assigned_to"] and order.status == WorkOrderStatus.OPEN.value:
        data.setdefault("status", WorkOrderStatus.ASSIGNED.value)
    for key, value in data.items():
        setattr(order, key, value)
    await write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="work_order.updated",
        entity_type="work_order",
        entity_id=order.id,
        old_value={"status": old_status},
        new_value={"status": order.status},
    )
    await db.commit()
    await db.refresh(order)
    return order
