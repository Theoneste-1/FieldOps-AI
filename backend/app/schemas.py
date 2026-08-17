from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserOut"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_id: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    organization_id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    status: str
    team_id: Optional[str] = None
    employee_code: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: str = "inspector"
    phone: Optional[str] = None
    team_id: Optional[str] = None
    employee_code: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    team_id: Optional[str] = None


class OrganizationOut(BaseModel):
    id: str
    name: str
    slug: str
    industry: str
    timezone: str
    settings: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class LocationOut(BaseModel):
    id: str
    name: str
    location_type: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    parent_id: Optional[str] = None

    model_config = {"from_attributes": True}


class AssetTypeOut(BaseModel):
    id: str
    code: str
    name: str
    category: str
    description: Optional[str] = None
    risk_config: dict[str, Any] = Field(default_factory=dict)
    measurement_thresholds: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class AssetOut(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    status: str
    asset_type_id: str
    location_id: Optional[str] = None
    parent_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    current_risk_level: str
    current_risk_score: int
    last_inspection_at: Optional[datetime] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
    asset_type: Optional[AssetTypeOut] = None
    location: Optional[LocationOut] = None

    model_config = {"from_attributes": True}


class AssetCreate(BaseModel):
    code: str
    name: str
    asset_type_id: str
    location_id: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None


class ObservationIn(BaseModel):
    field_key: str
    category: str = "other"
    label: str
    value_text: Optional[str] = None
    value_bool: Optional[bool] = None
    severity: Optional[str] = None
    structured: dict[str, Any] = Field(default_factory=dict)
    local_id: Optional[str] = None


class MeasurementIn(BaseModel):
    field_key: str
    label: str
    value: float
    unit: str = ""
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    local_id: Optional[str] = None


class ObservationOut(ObservationIn):
    id: str
    is_abnormal: Optional[bool] = None

    model_config = {"from_attributes": True}


class MeasurementOut(MeasurementIn):
    id: str
    is_abnormal: bool = False

    model_config = {"from_attributes": True}


class MediaOut(BaseModel):
    id: str
    media_type: str
    file_path: str
    mime_type: str
    size_bytes: int
    caption: Optional[str] = None
    url: Optional[str] = None

    model_config = {"from_attributes": True}


class RiskOut(BaseModel):
    id: str
    score: int
    level: str
    breakdown: list[dict[str, Any]] = Field(default_factory=list)
    rules_version: str
    calculated_at: datetime

    model_config = {"from_attributes": True}


class AIAnalysisOut(BaseModel):
    id: str
    status: str
    provider: str
    model: Optional[str] = None
    risk_summary: Optional[str] = None
    possible_causes: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    supervisor_brief: Optional[str] = None
    confidence: Optional[float] = None
    severity: Optional[str] = None
    used_fallback: bool = False
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class InspectionCreate(BaseModel):
    asset_id: str
    template_id: Optional[str] = None
    notes: Optional[str] = None
    weather: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    local_id: Optional[str] = None
    device_id: Optional[str] = None
    observations: list[ObservationIn] = Field(default_factory=list)
    measurements: list[MeasurementIn] = Field(default_factory=list)


class InspectionUpdate(BaseModel):
    notes: Optional[str] = None
    weather: Optional[str] = None
    status: Optional[str] = None
    observations: Optional[list[ObservationIn]] = None
    measurements: Optional[list[MeasurementIn]] = None
    version: Optional[int] = None


class InspectionOut(BaseModel):
    id: str
    organization_id: str
    asset_id: str
    template_id: Optional[str] = None
    inspector_id: str
    status: str
    notes: Optional[str] = None
    weather: Optional[str] = None
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    local_id: Optional[str] = None
    version: int
    sync_status: str
    asset: Optional[AssetOut] = None
    inspector: Optional[UserOut] = None
    observations: list[ObservationOut] = Field(default_factory=list)
    measurements: list[MeasurementOut] = Field(default_factory=list)
    media: list[MediaOut] = Field(default_factory=list)
    risk_assessment: Optional[RiskOut] = None
    ai_analysis: Optional[AIAnalysisOut] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewRequest(BaseModel):
    notes: Optional[str] = None
    resolve: bool = False


class WorkOrderCreate(BaseModel):
    asset_id: str
    inspection_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None
    due_at: Optional[datetime] = None


class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    due_at: Optional[datetime] = None
    completion_notes: Optional[str] = None


class WorkOrderOut(BaseModel):
    id: str
    organization_id: str
    inspection_id: Optional[str] = None
    asset_id: str
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    assigned_to: Optional[str] = None
    created_by: str
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    completion_notes: Optional[str] = None
    asset: Optional[AssetOut] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: str
    notification_type: str
    title: str
    body: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    user_id: str
    body: str
    created_at: datetime
    author: Optional[UserOut] = None

    model_config = {"from_attributes": True}


class SyncChange(BaseModel):
    local_id: str
    entity_type: str
    payload: dict[str, Any]
    updated_at: datetime
    version: int = 1
    client_deleted: bool = False


class SyncPushRequest(BaseModel):
    device_id: str
    platform: str = "android"
    app_version: Optional[str] = None
    changes: list[SyncChange] = Field(default_factory=list)


class SyncPushResult(BaseModel):
    local_id: str
    server_id: Optional[str] = None
    status: str
    message: Optional[str] = None
    server_version: Optional[int] = None


class SyncPullRequest(BaseModel):
    device_id: str
    since: Optional[datetime] = None
    entity_types: list[str] = Field(default_factory=lambda: ["assets", "inspections", "work_orders", "notifications"])


class TemplateOut(BaseModel):
    id: str
    name: str
    asset_type_id: Optional[str] = None
    version: int
    is_active: bool
    form_schema: dict[str, Any] = Field(validation_alias="schema", serialization_alias="schema")
    requires_photo: bool
    estimated_minutes: int

    model_config = {"from_attributes": True, "populate_by_name": True}


class KPIResponse(BaseModel):
    inspections_total: int
    inspections_completed: int
    inspections_pending: int
    critical_inspections: int
    high_inspections: int
    open_issues: int
    resolved_rate: float
    average_risk: float
    average_duration_minutes: float
    open_work_orders: int
    overdue_work_orders: int
    inspector_count: int
    asset_count: int
    due_inspections: int


class TimeSeriesPoint(BaseModel):
    date: str
    value: float
    label: Optional[str] = None


class NamedCount(BaseModel):
    name: str
    count: int
    extra: dict[str, Any] = Field(default_factory=dict)


class MapAssetOut(BaseModel):
    id: str
    code: str
    name: str
    latitude: float
    longitude: float
    current_risk_level: str
    current_risk_score: int
    status: str
    last_inspection_at: Optional[datetime] = None
    asset_type_name: Optional[str] = None


class AuditOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    old_value: Optional[dict[str, Any]] = None
    new_value: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class Page(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


TokenResponse.model_rebuild()
