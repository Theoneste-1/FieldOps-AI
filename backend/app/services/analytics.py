from datetime import timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    Asset,
    Inspection,
    InspectionSchedule,
    InspectionStatus,
    RiskAssessment,
    RiskLevel,
    User,
    WorkOrder,
    WorkOrderStatus,
)
from app.schemas import KPIResponse, NamedCount, TimeSeriesPoint
from app.services.common import utcnow


async def kpis(db: AsyncSession, organization_id: str) -> KPIResponse:
    now = utcnow()

    inspections_total = await _count(db, select(func.count(Inspection.id)).where(Inspection.organization_id == organization_id))
    completed = await _count(
        db,
        select(func.count(Inspection.id)).where(
            Inspection.organization_id == organization_id,
            Inspection.status.in_([InspectionStatus.ANALYZED.value, InspectionStatus.REVIEWED.value, InspectionStatus.RESOLVED.value]),
        ),
    )
    pending = await _count(
        db,
        select(func.count(Inspection.id)).where(
            Inspection.organization_id == organization_id,
            Inspection.status.in_([InspectionStatus.DRAFT.value, InspectionStatus.IN_PROGRESS.value, InspectionStatus.SUBMITTED.value, InspectionStatus.PROCESSING.value]),
        ),
    )
    critical = await _join_risk_count(db, organization_id, RiskLevel.CRITICAL.value)
    high = await _join_risk_count(db, organization_id, RiskLevel.HIGH.value)
    open_issues = await _count(
        db,
        select(func.count(Inspection.id)).where(
            Inspection.organization_id == organization_id,
            Inspection.status.notin_([InspectionStatus.RESOLVED.value]),
        ),
    )
    resolved = await _count(
        db,
        select(func.count(Inspection.id)).where(
            Inspection.organization_id == organization_id,
            Inspection.status == InspectionStatus.RESOLVED.value,
        ),
    )
    avg_risk = (
        await db.execute(
            select(func.avg(RiskAssessment.score))
            .join(Inspection, Inspection.id == RiskAssessment.inspection_id)
            .where(Inspection.organization_id == organization_id)
        )
    ).scalar() or 0
    avg_duration = (
        await db.execute(
            select(func.avg(Inspection.duration_minutes)).where(
                Inspection.organization_id == organization_id,
                Inspection.duration_minutes.is_not(None),
            )
        )
    ).scalar() or 0
    open_wo = await _count(
        db,
        select(func.count(WorkOrder.id)).where(
            WorkOrder.organization_id == organization_id,
            WorkOrder.status.in_([WorkOrderStatus.OPEN.value, WorkOrderStatus.ASSIGNED.value, WorkOrderStatus.IN_PROGRESS.value]),
        ),
    )
    overdue = await _count(
        db,
        select(func.count(WorkOrder.id)).where(
            WorkOrder.organization_id == organization_id,
            WorkOrder.due_at.is_not(None),
            WorkOrder.due_at < now,
            WorkOrder.status.notin_([WorkOrderStatus.COMPLETED.value, WorkOrderStatus.VERIFIED.value, WorkOrderStatus.CANCELLED.value]),
        ),
    )
    inspectors = await _count(db, select(func.count(User.id)).where(User.organization_id == organization_id, User.role == "inspector"))
    assets = await _count(db, select(func.count(Asset.id)).where(Asset.organization_id == organization_id))
    due = await _count(
        db,
        select(func.count(InspectionSchedule.id)).where(
            InspectionSchedule.organization_id == organization_id,
            InspectionSchedule.is_active.is_(True),
            InspectionSchedule.next_due_at <= now,
        ),
    )
    resolved_rate = round((resolved / inspections_total) * 100, 1) if inspections_total else 0.0
    return KPIResponse(
        inspections_total=inspections_total,
        inspections_completed=completed,
        inspections_pending=pending,
        critical_inspections=critical,
        high_inspections=high,
        open_issues=open_issues,
        resolved_rate=resolved_rate,
        average_risk=round(float(avg_risk), 1),
        average_duration_minutes=round(float(avg_duration), 1),
        open_work_orders=open_wo,
        overdue_work_orders=overdue,
        inspector_count=inspectors,
        asset_count=assets,
        due_inspections=due,
    )


async def inspections_over_time(db: AsyncSession, organization_id: str, days: int = 30) -> list[TimeSeriesPoint]:
    start = utcnow() - timedelta(days=days)
    stmt = (
        select(func.date(Inspection.created_at), func.count(Inspection.id))
        .where(Inspection.organization_id == organization_id, Inspection.created_at >= start)
        .group_by(func.date(Inspection.created_at))
        .order_by(func.date(Inspection.created_at))
    )
    rows = (await db.execute(stmt)).all()
    return [TimeSeriesPoint(date=str(day), value=float(count)) for day, count in rows]


async def risk_distribution(db: AsyncSession, organization_id: str) -> list[NamedCount]:
    stmt = (
        select(RiskAssessment.level, func.count(RiskAssessment.id))
        .join(Inspection, Inspection.id == RiskAssessment.inspection_id)
        .where(Inspection.organization_id == organization_id)
        .group_by(RiskAssessment.level)
    )
    rows = (await db.execute(stmt)).all()
    return [NamedCount(name=level, count=count) for level, count in rows]


async def issues_by_category(db: AsyncSession, organization_id: str) -> list[NamedCount]:
    from app.models.entities import Observation

    stmt = (
        select(Observation.category, func.count(Observation.id))
        .join(Inspection, Inspection.id == Observation.inspection_id)
        .where(Inspection.organization_id == organization_id)
        .group_by(Observation.category)
    )
    rows = (await db.execute(stmt)).all()
    return [NamedCount(name=category, count=count) for category, count in rows]


async def assets_by_risk(db: AsyncSession, organization_id: str) -> list[NamedCount]:
    stmt = (
        select(Asset.current_risk_level, func.count(Asset.id))
        .where(Asset.organization_id == organization_id)
        .group_by(Asset.current_risk_level)
    )
    rows = (await db.execute(stmt)).all()
    return [NamedCount(name=level, count=count) for level, count in rows]


async def inspector_productivity(db: AsyncSession, organization_id: str) -> list[NamedCount]:
    stmt = (
        select(User.full_name, func.count(Inspection.id), func.avg(Inspection.duration_minutes))
        .join(Inspection, Inspection.inspector_id == User.id)
        .where(Inspection.organization_id == organization_id)
        .group_by(User.full_name)
    )
    rows = (await db.execute(stmt)).all()
    return [
        NamedCount(name=name, count=count, extra={"average_duration_minutes": round(float(avg or 0), 1)})
        for name, count, avg in rows
    ]


async def resolution_time(db: AsyncSession, organization_id: str) -> list[TimeSeriesPoint]:
    stmt = (
        select(
            func.date(Inspection.resolved_at),
            func.avg(
                case(
                    (
                        Inspection.resolved_at.is_not(None) & Inspection.submitted_at.is_not(None),
                        func.extract("epoch", Inspection.resolved_at - Inspection.submitted_at) / 3600.0,
                    ),
                    else_=None,
                )
            ),
        )
        .where(Inspection.organization_id == organization_id, Inspection.resolved_at.is_not(None))
        .group_by(func.date(Inspection.resolved_at))
        .order_by(func.date(Inspection.resolved_at))
    )
    rows = (await db.execute(stmt)).all()
    return [TimeSeriesPoint(date=str(day), value=round(float(avg or 0), 2), label="hours") for day, avg in rows]


async def top_failing_assets(db: AsyncSession, organization_id: str, limit: int = 8) -> list[NamedCount]:
    stmt = (
        select(Asset.code, Asset.name, func.count(Inspection.id), func.avg(RiskAssessment.score))
        .join(Inspection, Inspection.asset_id == Asset.id)
        .join(RiskAssessment, RiskAssessment.inspection_id == Inspection.id)
        .where(
            Asset.organization_id == organization_id,
            RiskAssessment.level.in_([RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]),
        )
        .group_by(Asset.code, Asset.name)
        .order_by(func.count(Inspection.id).desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [
        NamedCount(name=f"{code} · {name}", count=count, extra={"average_risk": round(float(avg or 0), 1)})
        for code, name, count, avg in rows
    ]


async def _count(db: AsyncSession, stmt) -> int:
    return int((await db.execute(stmt)).scalar_one() or 0)


async def _join_risk_count(db: AsyncSession, organization_id: str, level: str) -> int:
    stmt = (
        select(func.count(RiskAssessment.id))
        .join(Inspection, Inspection.id == RiskAssessment.inspection_id)
        .where(Inspection.organization_id == organization_id, RiskAssessment.level == level)
    )
    return await _count(db, stmt)
