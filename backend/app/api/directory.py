from fastapi import APIRouter
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.deps import AdminUser, CurrentUser, DbSession, SupervisorUser
from app.exceptions import ConflictError
from app.models.entities import Asset, AssetType, Location, User, new_id
from app.schemas import AssetCreate, AssetOut, AssetTypeOut, LocationOut, UserCreate, UserOut, UserUpdate
from app.security import hash_password
from app.services.common import write_audit
from app.services.lookups import get_asset, get_user

router = APIRouter(tags=["Assets & Directory"])


@router.get("/asset-types", response_model=list[AssetTypeOut])
async def list_asset_types(user: CurrentUser, db: DbSession) -> list[AssetType]:
    stmt = select(AssetType).where(AssetType.organization_id == user.organization_id).order_by(AssetType.name)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/locations", response_model=list[LocationOut])
async def list_locations(user: CurrentUser, db: DbSession) -> list[Location]:
    stmt = select(Location).where(Location.organization_id == user.organization_id).order_by(Location.name)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/assets", response_model=list[AssetOut])
async def list_assets(
    user: CurrentUser,
    db: DbSession,
    q: str | None = None,
    risk: str | None = None,
    status: str | None = None,
    asset_type_id: str | None = None,
) -> list[Asset]:
    stmt = (
        select(Asset)
        .options(selectinload(Asset.asset_type), selectinload(Asset.location))
        .where(Asset.organization_id == user.organization_id)
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Asset.code.ilike(like), Asset.name.ilike(like)))
    if risk:
        stmt = stmt.where(Asset.current_risk_level == risk)
    if status:
        stmt = stmt.where(Asset.status == status)
    if asset_type_id:
        stmt = stmt.where(Asset.asset_type_id == asset_type_id)
    stmt = stmt.order_by(Asset.code)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/assets/{asset_id}", response_model=AssetOut)
async def get_asset_detail(asset_id: str, user: CurrentUser, db: DbSession) -> Asset:
    return await get_asset(db, user.organization_id, asset_id)


@router.post("/assets", response_model=AssetOut, status_code=201)
async def create_asset(payload: AssetCreate, user: SupervisorUser, db: DbSession) -> Asset:
    exists = (
        await db.execute(
            select(Asset).where(Asset.organization_id == user.organization_id, Asset.code == payload.code)
        )
    ).scalar_one_or_none()
    if exists:
        raise ConflictError(f"Asset code {payload.code} already exists")
    asset = Asset(id=new_id(), organization_id=user.organization_id, **payload.model_dump())
    db.add(asset)
    await write_audit(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="asset.created",
        entity_type="asset",
        entity_id=asset.id,
        new_value=payload.model_dump(),
    )
    await db.commit()
    return await get_asset(db, user.organization_id, asset.id)


@router.get("/users", response_model=list[UserOut])
async def list_users(user: CurrentUser, db: DbSession, role: str | None = None) -> list[User]:
    stmt = select(User).where(User.organization_id == user.organization_id)
    if role:
        stmt = stmt.where(User.role == role)
    return list((await db.execute(stmt)).scalars().all())


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(payload: UserCreate, user: AdminUser, db: DbSession) -> User:
    exists = (
        await db.execute(
            select(User).where(User.organization_id == user.organization_id, User.email == payload.email.lower())
        )
    ).scalar_one_or_none()
    if exists:
        raise ConflictError("Email already in use")
    created = User(
        id=new_id(),
        organization_id=user.organization_id,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        phone=payload.phone,
        team_id=payload.team_id,
        employee_code=payload.employee_code,
    )
    db.add(created)
    await db.commit()
    await db.refresh(created)
    return created


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: str, payload: UserUpdate, user: AdminUser, db: DbSession) -> User:
    target = await get_user(db, user.organization_id, user_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(target, key, value)
    await db.commit()
    await db.refresh(target)
    return target
