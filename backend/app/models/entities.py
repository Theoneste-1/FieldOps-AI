from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class UserRole(str, Enum):
    INSPECTOR = "inspector"
    SUPERVISOR = "supervisor"
    OPERATIONS_MANAGER = "operations_manager"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class AssetStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class InspectionStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    AI_FAILED = "ai_failed"
    PENDING_RETRY = "pending_retry"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"


class WorkOrderStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"


class WorkOrderPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, Enum):
    CRITICAL_RISK = "critical_risk"
    INSPECTION_REMINDER = "inspection_reminder"
    WORK_ORDER = "work_order"
    SYSTEM = "system"
    AI_COMPLETE = "ai_complete"
    ESCALATION = "escalation"


class ObservationCategory(str, Enum):
    TEMPERATURE = "temperature"
    LEAKAGE = "leakage"
    STRUCTURAL = "structural"
    NOISE = "noise"
    ELECTRICAL = "electrical"
    CORROSION = "corrosion"
    VEGETATION = "vegetation"
    SAFETY = "safety"
    MECHANICAL = "mechanical"
    ENVIRONMENTAL = "environmental"
    OTHER = "other"


class MediaType(str, Enum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SyncMixin:
    local_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    sync_status: Mapped[str] = mapped_column(String(20), default=SyncStatus.SYNCED.value)


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    industry: Mapped[str] = mapped_column(String(80), default="electrical")
    timezone: Mapped[str] = mapped_column(String(64), default="Africa/Johannesburg")
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[list[User]] = relationship(back_populates="organization")
    assets: Mapped[list[Asset]] = relationship(back_populates="organization")


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("organization_id", "email"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    role: Mapped[str] = mapped_column(String(40), default=UserRole.INSPECTOR.value)
    status: Mapped[str] = mapped_column(String(20), default=UserStatus.ACTIVE.value)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    team_id: Mapped[Optional[str]] = mapped_column(ForeignKey("teams.id"), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    employee_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="users")
    team: Mapped[Optional[Team]] = relationship(back_populates="members", foreign_keys="User.team_id")


class Team(TimestampMixin, Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    region: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    supervisor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)

    members: Mapped[list[User]] = relationship(
        back_populates="team",
        foreign_keys="User.team_id",
    )


class Location(TimestampMixin, Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("locations.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    location_type: Mapped[str] = mapped_column(String(40), default="site")  # region, site, zone
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)


class AssetType(TimestampMixin, Base):
    __tablename__ = "asset_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80), default="electrical")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_template_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    risk_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    measurement_thresholds: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class InspectionTemplate(TimestampMixin, Base):
    __tablename__ = "inspection_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    asset_type_id: Mapped[Optional[str]] = mapped_column(ForeignKey("asset_types.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    requires_photo: Mapped[bool] = mapped_column(Boolean, default=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=25)


class Asset(TimestampMixin, SyncMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("organization_id", "code"),
        Index("ix_assets_org_status", "organization_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    asset_type_id: Mapped[str] = mapped_column(ForeignKey("asset_types.id"), index=True)
    location_id: Mapped[Optional[str]] = mapped_column(ForeignKey("locations.id"), nullable=True)
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("assets.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(40), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=AssetStatus.ACTIVE.value)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    installed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_inspection_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_risk_level: Mapped[str] = mapped_column(String(20), default=RiskLevel.LOW.value)
    current_risk_score: Mapped[int] = mapped_column(Integer, default=0)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column("extra_json", JSON, default=dict)

    organization: Mapped[Organization] = relationship(back_populates="assets")
    asset_type: Mapped[AssetType] = relationship()
    location: Mapped[Optional[Location]] = relationship()
    inspections: Mapped[list[Inspection]] = relationship(back_populates="asset")


class InspectionSchedule(TimestampMixin, Base):
    __tablename__ = "inspection_schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    cadence_days: Mapped[int] = mapped_column(Integer, default=90)
    next_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sla_hours: Mapped[int] = mapped_column(Integer, default=48)


class Inspection(TimestampMixin, SyncMixin, Base):
    __tablename__ = "inspections"
    __table_args__ = (Index("ix_inspections_org_status", "organization_id", "status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    template_id: Mapped[Optional[str]] = mapped_column(ForeignKey("inspection_templates.id"), nullable=True)
    inspector_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    reviewer_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=InspectionStatus.DRAFT.value, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weather: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="inspections")
    inspector: Mapped[User] = relationship(foreign_keys=[inspector_id])
    observations: Mapped[list[Observation]] = relationship(back_populates="inspection", cascade="all, delete-orphan")
    measurements: Mapped[list[Measurement]] = relationship(back_populates="inspection", cascade="all, delete-orphan")
    media: Mapped[list[MediaItem]] = relationship(back_populates="inspection", cascade="all, delete-orphan")
    risk_assessment: Mapped[Optional[RiskAssessment]] = relationship(back_populates="inspection", uselist=False)
    ai_analysis: Mapped[Optional[AIAnalysis]] = relationship(back_populates="inspection", uselist=False)


class Observation(TimestampMixin, SyncMixin, Base):
    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), index=True)
    field_key: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(40), default=ObservationCategory.OTHER.value)
    label: Mapped[str] = mapped_column(String(160))
    value_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_bool: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    structured: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    inspection: Mapped[Inspection] = relationship(back_populates="observations")


class Measurement(TimestampMixin, SyncMixin, Base):
    __tablename__ = "measurements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), index=True)
    field_key: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(String(160))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default="")
    min_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False)

    inspection: Mapped[Inspection] = relationship(back_populates="measurements")


class MediaItem(TimestampMixin, SyncMixin, Base):
    __tablename__ = "media_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), index=True)
    media_type: Mapped[str] = mapped_column(String(20), default=MediaType.PHOTO.value)
    file_path: Mapped[str] = mapped_column(String(500))
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(80), default="image/jpeg")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    inspection: Mapped[Inspection] = relationship(back_populates="media")


class RiskAssessment(TimestampMixin, Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), unique=True)
    score: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(20), index=True)
    breakdown: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    rules_version: Mapped[str] = mapped_column(String(20), default="1.0")
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    inspection: Mapped[Inspection] = relationship(back_populates="risk_assessment")


class AIAnalysis(TimestampMixin, Base):
    __tablename__ = "ai_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    provider: Mapped[str] = mapped_column(String(40), default="gemini")
    model: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(20), default="1.0")
    risk_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    possible_causes: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list)
    supervisor_brief: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    used_fallback: Mapped[bool] = mapped_column(Boolean, default=False)

    inspection: Mapped[Inspection] = relationship(back_populates="ai_analysis")


class WorkOrder(TimestampMixin, SyncMixin, Base):
    __tablename__ = "work_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    inspection_id: Mapped[Optional[str]] = mapped_column(ForeignKey("inspections.id"), nullable=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default=WorkOrderPriority.MEDIUM.value)
    status: Mapped[str] = mapped_column(String(30), default=WorkOrderStatus.OPEN.value, index=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    completion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    asset: Mapped[Asset] = relationship()
    inspection: Mapped[Optional[Inspection]] = relationship()
    assignee: Mapped[Optional[User]] = relationship(foreign_keys=[assigned_to])


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    notification_type: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_org_created", "organization_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    old_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)

    author: Mapped[User] = relationship()


class SyncDevice(TimestampMixin, Base):
    __tablename__ = "sync_devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    device_id: Mapped[str] = mapped_column(String(80), index=True)
    platform: Mapped[str] = mapped_column(String(40), default="android")
    app_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_pull_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_push_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[str] = mapped_column(String(20), default=SyncStatus.SYNCED.value)
