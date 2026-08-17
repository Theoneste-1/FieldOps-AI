from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.deps import CurrentUser, DbSession, SupervisorUser
from app.exceptions import NotFoundError, ValidationAppError
from app.models.entities import Inspection, InspectionTemplate, MediaItem, MediaType, new_id
from app.schemas import (
    InspectionCreate,
    InspectionOut,
    InspectionUpdate,
    ReviewRequest,
    TemplateOut,
)
from app.services.inspections import (
    calculate_and_store_risk,
    create_inspection,
    review_inspection,
    retry_ai,
    submit_inspection,
    update_inspection,
)
from app.services.lookups import get_inspection

router = APIRouter(tags=["Inspections"])


@router.get("/templates", response_model=list[TemplateOut])
async def list_templates(user: CurrentUser, db: DbSession, asset_type_id: str | None = None) -> list[InspectionTemplate]:
    stmt = select(InspectionTemplate).where(
        InspectionTemplate.organization_id == user.organization_id,
        InspectionTemplate.is_active.is_(True),
    )
    if asset_type_id:
        stmt = stmt.where(InspectionTemplate.asset_type_id == asset_type_id)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/inspections", response_model=list[InspectionOut])
async def list_inspections(
    user: CurrentUser,
    db: DbSession,
    status: str | None = None,
    asset_id: str | None = None,
    inspector_id: str | None = None,
    risk: str | None = None,
) -> list[Inspection]:
    stmt = (
        select(Inspection)
        .options(
            selectinload(Inspection.observations),
            selectinload(Inspection.measurements),
            selectinload(Inspection.media),
            selectinload(Inspection.risk_assessment),
            selectinload(Inspection.ai_analysis),
            selectinload(Inspection.asset),
            selectinload(Inspection.inspector),
        )
        .where(Inspection.organization_id == user.organization_id)
    )
    if user.role == "inspector":
        stmt = stmt.where(Inspection.inspector_id == user.id)
    if status:
        stmt = stmt.where(Inspection.status == status)
    if asset_id:
        stmt = stmt.where(Inspection.asset_id == asset_id)
    if inspector_id:
        stmt = stmt.where(Inspection.inspector_id == inspector_id)
    if risk:
        from app.models.entities import RiskAssessment

        stmt = stmt.join(Inspection.risk_assessment).where(RiskAssessment.level == risk)
    stmt = stmt.order_by(Inspection.created_at.desc())
    return list((await db.execute(stmt)).scalars().unique().all())


@router.post("/inspections", response_model=InspectionOut, status_code=201)
async def create(payload: InspectionCreate, user: CurrentUser, db: DbSession) -> Inspection:
    return await create_inspection(db, user, payload)


@router.get("/inspections/{inspection_id}", response_model=InspectionOut)
async def detail(inspection_id: str, user: CurrentUser, db: DbSession) -> Inspection:
    return await get_inspection(db, user.organization_id, inspection_id)


@router.patch("/inspections/{inspection_id}", response_model=InspectionOut)
async def update(inspection_id: str, payload: InspectionUpdate, user: CurrentUser, db: DbSession) -> Inspection:
    return await update_inspection(db, user, inspection_id, payload)


@router.post("/inspections/{inspection_id}/submit", response_model=InspectionOut)
async def submit(inspection_id: str, user: CurrentUser, db: DbSession) -> Inspection:
    return await submit_inspection(db, user, inspection_id)


@router.post("/inspections/{inspection_id}/risk/calculate", response_model=InspectionOut)
async def recalc_risk(inspection_id: str, user: CurrentUser, db: DbSession) -> Inspection:
    inspection = await get_inspection(db, user.organization_id, inspection_id)
    await calculate_and_store_risk(db, inspection)
    await db.commit()
    return await get_inspection(db, user.organization_id, inspection_id)


@router.post("/inspections/{inspection_id}/ai/analyze", response_model=InspectionOut)
async def analyze(inspection_id: str, user: CurrentUser, db: DbSession) -> Inspection:
    return await retry_ai(db, user, inspection_id)


@router.post("/inspections/{inspection_id}/review", response_model=InspectionOut)
async def review(inspection_id: str, payload: ReviewRequest, user: SupervisorUser, db: DbSession) -> Inspection:
    return await review_inspection(db, user, inspection_id, payload.notes, payload.resolve)


@router.post("/inspections/{inspection_id}/media", response_model=InspectionOut)
async def upload_media(
    inspection_id: str,
    user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
    caption: str | None = Form(None),
) -> Inspection:
    inspection = await get_inspection(db, user.organization_id, inspection_id)
    settings = get_settings()
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise ValidationAppError(f"File exceeds {settings.max_upload_mb} MB")
    folder = settings.upload_path / inspection.organization_id / inspection.id
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "photo.jpg").suffix or ".jpg"
    stored = folder / f"{new_id()}{suffix}"
    stored.write_bytes(data)
    item = MediaItem(
        id=new_id(),
        inspection_id=inspection.id,
        media_type=MediaType.PHOTO.value,
        file_path=str(stored),
        mime_type=file.content_type or "image/jpeg",
        size_bytes=len(data),
        caption=caption,
    )
    db.add(item)
    await db.commit()
    return await get_inspection(db, user.organization_id, inspection_id)


@router.get("/media/{media_id}/file")
async def get_media_file(media_id: str, user: CurrentUser, db: DbSession) -> FileResponse:
    item = await db.get(MediaItem, media_id)
    if item is None:
        raise NotFoundError("Media", media_id)
    inspection = await db.get(Inspection, item.inspection_id)
    if inspection is None or inspection.organization_id != user.organization_id:
        raise NotFoundError("Media", media_id)
    path = Path(item.file_path)
    if not path.exists():
        raise NotFoundError("Media file", media_id)
    return FileResponse(path, media_type=item.mime_type)
