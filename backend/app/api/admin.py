from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession, SupervisorUser
from app.engines.risk import DEFAULT_RULES, DEFAULT_THRESHOLDS, LEVEL_BANDS, RULES_VERSION
from app.models.entities import Inspection, InspectionTemplate

router = APIRouter(tags=["Admin & Export"])


@router.get("/risk/rules")
async def risk_rules(user: CurrentUser) -> dict:
    return {
        "version": RULES_VERSION,
        "bands": [{"max": upper, "level": level.value} for upper, level in LEVEL_BANDS],
        "rules": [
            {"key": rule.key, "label": rule.label, "weight": rule.weight, "description": rule.description}
            for rule in DEFAULT_RULES
        ],
        "default_thresholds": DEFAULT_THRESHOLDS,
        "principle": "AI assists decision-making; AI does not control critical business rules.",
    }


@router.get("/admin/templates")
async def admin_templates(user: SupervisorUser, db: DbSession):
    stmt = select(InspectionTemplate).where(InspectionTemplate.organization_id == user.organization_id)
    items = list((await db.execute(stmt)).scalars().all())
    return [
        {
            "id": item.id,
            "name": item.name,
            "version": item.version,
            "is_active": item.is_active,
            "schema": item.schema,
            "requires_photo": item.requires_photo,
        }
        for item in items
    ]


@router.get("/export/inspections.csv")
async def export_inspections(user: SupervisorUser, db: DbSession) -> StreamingResponse:
    stmt = (
        select(Inspection)
        .options(
            selectinload(Inspection.asset),
            selectinload(Inspection.inspector),
            selectinload(Inspection.risk_assessment),
        )
        .where(Inspection.organization_id == user.organization_id)
        .order_by(Inspection.created_at.desc())
    )
    rows = list((await db.execute(stmt)).scalars().unique().all())
    lines = ["id,asset_code,inspector,status,risk_level,risk_score,submitted_at"]
    for item in rows:
        risk = item.risk_assessment
        lines.append(
            ",".join(
                [
                    item.id,
                    item.asset.code if item.asset else "",
                    item.inspector.full_name if item.inspector else "",
                    item.status,
                    risk.level if risk else "",
                    str(risk.score if risk else ""),
                    item.submitted_at.isoformat() if item.submitted_at else "",
                ]
            )
        )
    content = "\n".join(lines)

    def iterator():
        yield content

    return StreamingResponse(
        iterator(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inspections.csv"},
    )
