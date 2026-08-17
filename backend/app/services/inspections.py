from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.service import run_analysis
from app.config import get_settings
from app.engines.lifecycle import InspectionStateMachine
from app.engines.risk import RULES_VERSION, calculate_risk
from app.metrics import inspection_submission_total, risk_calculations_total, work_orders_created_total
from app.models.entities import (
    AIAnalysis,
    Asset,
    Inspection,
    InspectionStatus,
    Measurement,
    NotificationType,
    Observation,
    RiskAssessment,
    RiskLevel,
    User,
    UserRole,
    WorkOrder,
    WorkOrderPriority,
    WorkOrderStatus,
    new_id,
)
from app.schemas import InspectionCreate, InspectionUpdate, ObservationIn, MeasurementIn
from app.services.common import notify_users, utcnow, write_audit
from app.services.lookups import get_asset, get_inspection


def _obs_dicts(items: list[Observation] | list[ObservationIn]) -> list[dict]:
    result = []
    for item in items:
        if isinstance(item, ObservationIn):
            result.append(item.model_dump())
        else:
            result.append(
                {
                    "field_key": item.field_key,
                    "category": item.category,
                    "label": item.label,
                    "value_text": item.value_text,
                    "value_bool": item.value_bool,
                    "severity": item.severity,
                }
            )
    return result


def _meas_dicts(items: list[Measurement] | list[MeasurementIn]) -> list[dict]:
    result = []
    for item in items:
        if isinstance(item, MeasurementIn):
            result.append(item.model_dump())
        else:
            result.append(
                {
                    "field_key": item.field_key,
                    "label": item.label,
                    "value": item.value,
                    "unit": item.unit,
                    "min_threshold": item.min_threshold,
                    "max_threshold": item.max_threshold,
                }
            )
    return result


def _replace_children(inspection: Inspection, observations: list[ObservationIn] | None, measurements: list[MeasurementIn] | None) -> None:
    if observations is not None:
        inspection.observations.clear()
        for item in observations:
            inspection.observations.append(
                Observation(
                    id=new_id(),
                    inspection_id=inspection.id,
                    field_key=item.field_key,
                    category=item.category,
                    label=item.label,
                    value_text=item.value_text,
                    value_bool=item.value_bool,
                    severity=item.severity,
                    structured=item.structured,
                    local_id=item.local_id,
                )
            )
    if measurements is not None:
        inspection.measurements.clear()
        for item in measurements:
            inspection.measurements.append(
                Measurement(
                    id=new_id(),
                    inspection_id=inspection.id,
                    field_key=item.field_key,
                    label=item.label,
                    value=item.value,
                    unit=item.unit,
                    min_threshold=item.min_threshold,
                    max_threshold=item.max_threshold,
                    local_id=item.local_id,
                )
            )


async def previous_failure_count(db: AsyncSession, asset_id: str, exclude_id: str | None = None) -> int:
    cutoff = utcnow() - timedelta(days=180)
    stmt = (
        select(func.count(RiskAssessment.id))
        .join(Inspection, Inspection.id == RiskAssessment.inspection_id)
        .where(
            Inspection.asset_id == asset_id,
            Inspection.created_at >= cutoff,
            RiskAssessment.level.in_([RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]),
        )
    )
    if exclude_id:
        stmt = stmt.where(Inspection.id != exclude_id)
    return int((await db.execute(stmt)).scalar_one() or 0)


async def create_inspection(db: AsyncSession, user: User, payload: InspectionCreate) -> Inspection:
    asset = await get_asset(db, user.organization_id, payload.asset_id)
    inspection = Inspection(
        id=new_id(),
        organization_id=user.organization_id,
        asset_id=asset.id,
        template_id=payload.template_id,
        inspector_id=user.id,
        status=InspectionStatus.IN_PROGRESS.value,
        notes=payload.notes,
        weather=payload.weather,
        started_at=utcnow(),
        latitude=payload.latitude or asset.latitude,
        longitude=payload.longitude or asset.longitude,
        local_id=payload.local_id,
        device_id=payload.device_id,
        sync_status="synced",
    )
    db.add(inspection)
    await db.flush()
    _replace_children(inspection, payload.observations, payload.measurements)
    await write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="inspection.created",
        entity_type="inspection",
        entity_id=inspection.id,
        new_value={"asset_id": asset.id, "status": inspection.status},
    )
    await db.commit()
    return await get_inspection(db, user.organization_id, inspection.id)


async def update_inspection(db: AsyncSession, user: User, inspection_id: str, payload: InspectionUpdate) -> Inspection:
    inspection = await get_inspection(db, user.organization_id, inspection_id)
    if not InspectionStateMachine.is_editable(inspection.status):
        from app.exceptions import InvalidStateError

        raise InvalidStateError("Only draft or in-progress inspections can be edited")
    if payload.notes is not None:
        inspection.notes = payload.notes
    if payload.weather is not None:
        inspection.weather = payload.weather
    _replace_children(inspection, payload.observations, payload.measurements)
    inspection.version += 1
    inspection.updated_at = utcnow()
    await db.commit()
    return await get_inspection(db, user.organization_id, inspection.id)


async def calculate_and_store_risk(db: AsyncSession, inspection: Inspection) -> RiskAssessment:
    asset = inspection.asset
    prev = await previous_failure_count(db, inspection.asset_id, inspection.id)
    thresholds = (asset.asset_type.measurement_thresholds if asset and asset.asset_type else {}) or {}
    risk_config = (asset.asset_type.risk_config if asset and asset.asset_type else {}) or {}
    meas = _meas_dicts(inspection.measurements)
    result = calculate_risk(
        observations=_obs_dicts(inspection.observations),
        measurements=meas,
        previous_high_or_critical=prev,
        risk_config=risk_config,
        measurement_thresholds=thresholds,
    )
    for measurement, computed in zip(inspection.measurements, meas):
        measurement.is_abnormal = bool(computed.get("is_abnormal"))
        if measurement.min_threshold is None and measurement.field_key in thresholds:
            measurement.min_threshold = thresholds[measurement.field_key].get("min")
        if measurement.max_threshold is None and measurement.field_key in thresholds:
            measurement.max_threshold = thresholds[measurement.field_key].get("max")

    if inspection.risk_assessment:
        assessment = inspection.risk_assessment
        assessment.score = result.score
        assessment.level = result.level.value
        assessment.breakdown = result.breakdown
        assessment.rules_version = RULES_VERSION
        assessment.calculated_at = utcnow()
    else:
        assessment = RiskAssessment(
            id=new_id(),
            inspection_id=inspection.id,
            score=result.score,
            level=result.level.value,
            breakdown=result.breakdown,
            rules_version=RULES_VERSION,
        )
        db.add(assessment)
        inspection.risk_assessment = assessment

    if asset:
        asset.current_risk_score = result.score
        asset.current_risk_level = result.level.value
        asset.last_inspection_at = utcnow()
    risk_calculations_total.labels(level=result.level.value).inc()
    return assessment


async def submit_inspection(db: AsyncSession, user: User, inspection_id: str) -> Inspection:
    inspection = await get_inspection(db, user.organization_id, inspection_id)
    InspectionStateMachine.transition(inspection.status, InspectionStatus.SUBMITTED.value)
    inspection.status = InspectionStatus.SUBMITTED.value
    inspection.submitted_at = utcnow()
    if inspection.started_at:
        inspection.duration_minutes = max(1, int((inspection.submitted_at - inspection.started_at).total_seconds() // 60))
    inspection.status = InspectionStateMachine.transition(inspection.status, InspectionStatus.PROCESSING.value)
    assessment = await calculate_and_store_risk(db, inspection)
    inspection_submission_total.labels(risk_level=assessment.level).inc()
    await db.flush()

    context = {
        "asset_code": inspection.asset.code if inspection.asset else None,
        "asset_name": inspection.asset.name if inspection.asset else None,
        "asset_type": inspection.asset.asset_type.name if inspection.asset and inspection.asset.asset_type else None,
        "asset_category": inspection.asset.asset_type.category if inspection.asset and inspection.asset.asset_type else None,
        "risk_score": assessment.score,
        "risk_level": assessment.level,
        "risk_breakdown": assessment.breakdown,
        "observations": _obs_dicts(inspection.observations),
        "measurements": _meas_dicts(inspection.measurements),
        "notes": inspection.notes,
        "weather": inspection.weather,
        "previous_high_or_critical": await previous_failure_count(db, inspection.asset_id, inspection.id),
    }
    try:
        ai_result = await run_analysis(context)
        target = InspectionStatus.ANALYZED.value
        error = ai_result.get("error_message")
    except Exception as exc:  # noqa: BLE001
        ai_result = {
            "status": "failed",
            "provider": "gemini",
            "model": None,
            "prompt_version": "1.1",
            "risk_summary": None,
            "possible_causes": [],
            "recommendations": [],
            "supervisor_brief": None,
            "confidence": None,
            "severity": None,
            "raw_response": None,
            "latency_ms": None,
            "used_fallback": False,
            "error_message": str(exc),
            "retry_count": 0,
        }
        target = InspectionStatus.AI_FAILED.value
        error = str(exc)

    if inspection.ai_analysis:
        analysis = inspection.ai_analysis
        for key, value in ai_result.items():
            if hasattr(analysis, key):
                setattr(analysis, key, value)
    else:
        analysis = AIAnalysis(id=new_id(), inspection_id=inspection.id, **{k: v for k, v in ai_result.items() if k != "retry_count"}, retry_count=ai_result.get("retry_count", 0))
        db.add(analysis)

    inspection.status = InspectionStateMachine.transition(inspection.status, target)
    inspection.analyzed_at = utcnow() if target == InspectionStatus.ANALYZED.value else None

    await _after_submit_side_effects(db, user, inspection, assessment)
    await write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="inspection.submitted",
        entity_type="inspection",
        entity_id=inspection.id,
        new_value={"status": inspection.status, "risk": assessment.level, "score": assessment.score, "ai_error": error},
    )
    await db.commit()
    return await get_inspection(db, user.organization_id, inspection.id)


async def retry_ai(db: AsyncSession, user: User, inspection_id: str) -> Inspection:
    inspection = await get_inspection(db, user.organization_id, inspection_id)
    if inspection.status not in {InspectionStatus.AI_FAILED.value, InspectionStatus.PENDING_RETRY.value, InspectionStatus.ANALYZED.value}:
        from app.exceptions import InvalidStateError

        raise InvalidStateError("AI retry is only available after analysis has been attempted")
    if inspection.status == InspectionStatus.AI_FAILED.value:
        inspection.status = InspectionStateMachine.transition(inspection.status, InspectionStatus.PENDING_RETRY.value)
    if inspection.status == InspectionStatus.PENDING_RETRY.value:
        inspection.status = InspectionStateMachine.transition(inspection.status, InspectionStatus.PROCESSING.value)
    await db.flush()
    # Re-enter submit pipeline from processing.
    inspection.status = InspectionStatus.SUBMITTED.value
    await db.commit()
    return await submit_inspection(db, user, inspection_id)


async def review_inspection(db: AsyncSession, user: User, inspection_id: str, notes: str | None, resolve: bool) -> Inspection:
    inspection = await get_inspection(db, user.organization_id, inspection_id)
    if inspection.status in {InspectionStatus.ANALYZED.value, InspectionStatus.AI_FAILED.value}:
        inspection.status = InspectionStateMachine.transition(inspection.status, InspectionStatus.REVIEWED.value)
    inspection.reviewer_id = user.id
    inspection.reviewed_at = utcnow()
    inspection.review_notes = notes
    if resolve:
        inspection.status = InspectionStateMachine.transition(inspection.status, InspectionStatus.RESOLVED.value)
        inspection.resolved_at = utcnow()
    await write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="inspection.reviewed",
        entity_type="inspection",
        entity_id=inspection.id,
        new_value={"status": inspection.status, "notes": notes},
    )
    await db.commit()
    return await get_inspection(db, user.organization_id, inspection.id)


async def _after_submit_side_effects(db: AsyncSession, user: User, inspection: Inspection, assessment: RiskAssessment) -> None:
    settings = get_settings()
    org_users = list(
        (
            await db.execute(
                select(User).where(
                    User.organization_id == user.organization_id,
                    User.role.in_([UserRole.SUPERVISOR.value, UserRole.OPERATIONS_MANAGER.value, UserRole.ADMIN.value]),
                )
            )
        ).scalars().all()
    )
    asset_code = inspection.asset.code if inspection.asset else "asset"
    if assessment.level == RiskLevel.CRITICAL.value:
        await notify_users(
            db,
            organization_id=user.organization_id,
            users=org_users,
            notification_type=NotificationType.CRITICAL_RISK.value,
            title=f"Critical inspection detected for {asset_code}",
            body=f"{user.full_name} submitted a CRITICAL inspection ({assessment.score}/100) for {asset_code}.",
            entity_type="inspection",
            entity_id=inspection.id,
        )
        if settings.auto_create_work_order_on_critical:
            existing = (
                await db.execute(
                    select(WorkOrder).where(
                        WorkOrder.inspection_id == inspection.id,
                        WorkOrder.status.notin_([WorkOrderStatus.CANCELLED.value, WorkOrderStatus.VERIFIED.value]),
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                order = WorkOrder(
                    id=new_id(),
                    organization_id=user.organization_id,
                    inspection_id=inspection.id,
                    asset_id=inspection.asset_id,
                    title=f"Follow-up: {asset_code} critical finding",
                    description="Auto-created from a critical inspection. A supervisor must assign and approve work.",
                    priority=WorkOrderPriority.CRITICAL.value,
                    status=WorkOrderStatus.OPEN.value,
                    created_by=user.id,
                    due_at=utcnow() + timedelta(hours=24),
                )
                db.add(order)
                work_orders_created_total.labels(priority=WorkOrderPriority.CRITICAL.value).inc()
    elif assessment.level == RiskLevel.HIGH.value:
        await notify_users(
            db,
            organization_id=user.organization_id,
            users=org_users,
            notification_type=NotificationType.SYSTEM.value,
            title=f"High-risk inspection for {asset_code}",
            body=f"Risk score {assessment.score}/100. Supervisor review recommended.",
            entity_type="inspection",
            entity_id=inspection.id,
        )
