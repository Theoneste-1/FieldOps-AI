"""Idempotent demo tenant: Helios Grid Operations.

The seed is designed so a buyer or interviewer can log in immediately and walk
the transformer T-104 critical-inspection story without configuring anything.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import select

from app.database import SessionLocal
from app.engines.risk import calculate_risk
from app.logging import get_logger
from app.models.entities import (
    AIAnalysis,
    Asset,
    AssetType,
    Inspection,
    InspectionSchedule,
    InspectionStatus,
    InspectionTemplate,
    Location,
    Measurement,
    Notification,
    NotificationType,
    Observation,
    Organization,
    RiskAssessment,
    Team,
    User,
    WorkOrder,
    WorkOrderPriority,
    WorkOrderStatus,
    new_id,
)
from app.security import hash_password
from app.services.common import utcnow

logger = get_logger("seed")

DEMO_PASSWORD = "Demo@12345"
ORG_SLUG = "helios-grid"


TRANSFORMER_TEMPLATE: dict[str, Any] = {
    "fields": [
        {"key": "temperature", "type": "number", "label": "Operating temperature", "unit": "°C", "required": True, "max": 80},
        {"key": "oil_leakage", "type": "boolean", "label": "Oil leakage", "category": "leakage", "required": True},
        {"key": "noise", "type": "enum", "label": "Noise level", "options": ["normal", "elevated", "high"], "category": "noise"},
        {"key": "visual_damage", "type": "boolean", "label": "Visual / structural damage", "category": "structural"},
        {"key": "load", "type": "number", "label": "Load", "unit": "%", "max": 90},
        {"key": "vibration", "type": "number", "label": "Vibration", "unit": "mm/s", "max": 7.1},
        {"key": "immediate_danger", "type": "boolean", "label": "Immediate danger", "category": "safety"},
        {"key": "notes", "type": "text", "label": "Free-text observation"},
    ],
    "required_photos": 1,
}


async def seed_if_needed() -> None:
    async with SessionLocal() as db:
        existing = (await db.execute(select(Organization).where(Organization.slug == ORG_SLUG))).scalar_one_or_none()
        if existing:
            logger.info("seed_skipped", reason="organization already exists")
            return
        await seed_demo(db)
        await db.commit()
        logger.info("seed_completed", org=ORG_SLUG, password=DEMO_PASSWORD)


async def seed_demo(db) -> None:
    now = utcnow()
    org = Organization(
        id=new_id(),
        name="Helios Grid Operations",
        slug=ORG_SLUG,
        industry="electrical",
        timezone="Africa/Johannesburg",
        settings={
            "auto_create_work_order_on_critical": True,
            "critical_review_sla_hours": 4,
            "brand_primary": "#0F3D3E",
        },
    )
    db.add(org)
    await db.flush()

    team = Team(id=new_id(), organization_id=org.id, name="Johannesburg North Crew", region="Gauteng")
    db.add(team)
    await db.flush()

    users = {
        "inspector": User(
            id=new_id(),
            organization_id=org.id,
            email="inspector@fieldops.ai",
            password_hash=hash_password(DEMO_PASSWORD),
            full_name="Thabo Mokoena",
            role="inspector",
            phone="+27 82 100 1001",
            team_id=team.id,
            employee_code="INS-014",
        ),
        "inspector2": User(
            id=new_id(),
            organization_id=org.id,
            email="inspector2@fieldops.ai",
            password_hash=hash_password(DEMO_PASSWORD),
            full_name="Aisha Naidoo",
            role="inspector",
            phone="+27 82 100 1002",
            team_id=team.id,
            employee_code="INS-021",
        ),
        "supervisor": User(
            id=new_id(),
            organization_id=org.id,
            email="supervisor@fieldops.ai",
            password_hash=hash_password(DEMO_PASSWORD),
            full_name="Lerato Dlamini",
            role="supervisor",
            phone="+27 82 200 2002",
            team_id=team.id,
            employee_code="SUP-007",
        ),
        "manager": User(
            id=new_id(),
            organization_id=org.id,
            email="manager@fieldops.ai",
            password_hash=hash_password(DEMO_PASSWORD),
            full_name="Pieter van Wyk",
            role="operations_manager",
            phone="+27 82 300 3003",
            employee_code="OPS-001",
        ),
        "admin": User(
            id=new_id(),
            organization_id=org.id,
            email="admin@fieldops.ai",
            password_hash=hash_password(DEMO_PASSWORD),
            full_name="Nomsa Khumalo",
            role="admin",
            phone="+27 82 400 4004",
            employee_code="ADM-001",
        ),
    }
    for user in users.values():
        db.add(user)
    team.supervisor_id = users["supervisor"].id
    await db.flush()

    region = Location(
        id=new_id(),
        organization_id=org.id,
        name="Gauteng North",
        location_type="region",
        region="Gauteng",
        latitude=-26.10,
        longitude=28.05,
    )
    db.add(region)
    await db.flush()
    sites = []
    site_defs = [
        ("Sandton Substation", "12 Rivonia Rd, Sandton", -26.1076, 28.0567),
        ("Midrand Switching Yard", "Olivenhoutbosch Rd, Midrand", -25.9992, 28.1260),
        ("Alexandra Feeder Hub", "London Rd, Alexandra", -26.1035, 28.0987),
        ("Rosebank Distribution", "Oxford Rd, Rosebank", -26.1450, 28.0416),
    ]
    for name, address, lat, lng in site_defs:
        loc = Location(
            id=new_id(),
            organization_id=org.id,
            parent_id=region.id,
            name=name,
            location_type="site",
            address=address,
            latitude=lat,
            longitude=lng,
            region="Gauteng",
        )
        db.add(loc)
        sites.append(loc)
    await db.flush()

    transformer_type = AssetType(
        id=new_id(),
        organization_id=org.id,
        code="TX",
        name="Distribution Transformer",
        category="electrical",
        description="Oil-filled medium-voltage distribution transformer",
        measurement_thresholds={
            "temperature": {"max": 80, "unit": "°C"},
            "oil_temperature": {"max": 85, "unit": "°C"},
            "load": {"max": 90, "unit": "%"},
            "vibration": {"max": 7.1, "unit": "mm/s"},
        },
        risk_config={"weights": {}},
    )
    switchgear_type = AssetType(
        id=new_id(),
        organization_id=org.id,
        code="SG",
        name="Switchgear Bay",
        category="electrical",
        description="MV switchgear and protection bay",
        measurement_thresholds={"temperature": {"max": 70, "unit": "°C"}},
        risk_config={"weights": {}},
    )
    pole_type = AssetType(
        id=new_id(),
        organization_id=org.id,
        code="PL",
        name="Wood Pole / Overhead Line",
        category="electrical",
        description="Distribution pole and conductor span",
        measurement_thresholds={},
        risk_config={"weights": {"structural_damage": 25}},
    )
    db.add_all([transformer_type, switchgear_type, pole_type])
    await db.flush()

    template = InspectionTemplate(
        id=new_id(),
        organization_id=org.id,
        asset_type_id=transformer_type.id,
        name="MV Transformer Field Inspection",
        schema=TRANSFORMER_TEMPLATE,
        requires_photo=True,
        estimated_minutes=30,
    )
    db.add(template)
    transformer_type.default_template_id = template.id
    await db.flush()

    # Johannesburg-area coordinates, T-104 is the wow-demo asset.
    asset_defs = [
        ("T-101", "Sandton TX 1", transformer_type, sites[0], -26.1070, 28.0550, "low", 18),
        ("T-102", "Sandton TX 2", transformer_type, sites[0], -26.1082, 28.0581, "medium", 44),
        ("T-103", "Midrand TX 1", transformer_type, sites[1], -25.9984, 28.1244, "low", 12),
        ("T-104", "Midrand TX 4 — Critical demo", transformer_type, sites[1], -25.9998, 28.1288, "high", 72),
        ("T-105", "Alexandra TX 1", transformer_type, sites[2], -26.1028, 28.0971, "medium", 51),
        ("T-106", "Alexandra TX 2", transformer_type, sites[2], -26.1049, 28.1012, "low", 22),
        ("T-107", "Rosebank TX 1", transformer_type, sites[3], -26.1442, 28.0402, "low", 9),
        ("T-108", "Rosebank TX 2", transformer_type, sites[3], -26.1461, 28.0433, "high", 68),
        ("SG-12", "Sandton Bay 12", switchgear_type, sites[0], -26.1064, 28.0574, "medium", 40),
        ("SG-18", "Midrand Bay 18", switchgear_type, sites[1], -26.0004, 28.1271, "low", 16),
        ("PL-441", "Alexandra Pole 441", pole_type, sites[2], -26.1058, 28.0960, "medium", 38),
        ("PL-442", "Alexandra Pole 442", pole_type, sites[2], -26.1019, 28.1004, "low", 14),
    ]
    assets: dict[str, Asset] = {}
    for code, name, atype, site, lat, lng, risk, score in asset_defs:
        asset = Asset(
            id=new_id(),
            organization_id=org.id,
            asset_type_id=atype.id,
            location_id=site.id,
            code=code,
            name=name,
            description=f"{atype.name} serving {site.name}",
            status="active",
            latitude=lat,
            longitude=lng,
            installed_at=now - timedelta(days=1400),
            current_risk_level=risk,
            current_risk_score=score,
            manufacturer="Siemens" if code.startswith("T") else "ABB",
            serial_number=f"SN-{code}-2019",
            extra_metadata={"voltage_kv": 11 if code.startswith("T") else 22, "cooling": "ONAN" if code.startswith("T") else None},
        )
        db.add(asset)
        assets[code] = asset
        db.add(
            InspectionSchedule(
                id=new_id(),
                organization_id=org.id,
                asset_id=asset.id,
                cadence_days=90 if code.startswith("T") else 180,
                next_due_at=now + timedelta(days=12 if code == "T-104" else 40),
                sla_hours=24 if risk == "high" else 72,
            )
        )
    await db.flush()

    inspector = users["inspector"]
    inspector2 = users["inspector2"]

    historical = [
        # (days_ago, asset, inspector, temp, leak, noise, damage, notes, status)
        (40, "T-101", inspector, 62, False, "normal", False, "Routine inspection. Bushings clean.", InspectionStatus.RESOLVED.value),
        (28, "T-102", inspector2, 81, False, "elevated", False, "Temperature slightly high under peak load.", InspectionStatus.REVIEWED.value),
        (21, "T-105", inspector, 77, True, "normal", False, "Small oil weep at lower gasket.", InspectionStatus.ANALYZED.value),
        (14, "T-108", inspector2, 88, False, "high", True, "Cracked conservator bracket and loud hum.", InspectionStatus.REVIEWED.value),
        (10, "T-104", inspector, 84, False, "elevated", False, "Temperature climbing; no leak yet.", InspectionStatus.ANALYZED.value),
        (6, "SG-12", inspector, 66, False, "normal", False, "Protection flags clear.", InspectionStatus.RESOLVED.value),
        (3, "PL-441", inspector2, 0, False, "normal", True, "Split in pole at 2m. Hardware rusted.", InspectionStatus.ANALYZED.value),
        (1, "T-103", inspector, 58, False, "normal", False, "All readings nominal.", InspectionStatus.RESOLVED.value),
    ]

    for days_ago, code, who, temp, leak, noise, damage, notes, status in historical:
        asset = assets[code]
        created = now - timedelta(days=days_ago)
        observations = [
            Observation(
                id=new_id(),
                field_key="oil_leakage",
                category="leakage",
                label="Oil leakage",
                value_bool=leak,
                value_text="Yes" if leak else "No",
            ),
            Observation(
                id=new_id(),
                field_key="noise",
                category="noise",
                label="Noise level",
                value_text=noise,
                severity="high" if noise == "high" else "medium" if noise == "elevated" else "low",
            ),
            Observation(
                id=new_id(),
                field_key="visual_damage",
                category="structural",
                label="Visual damage",
                value_bool=damage,
                value_text="Yes" if damage else "No",
            ),
        ]
        measurements = []
        if temp:
            measurements.append(
                Measurement(
                    id=new_id(),
                    field_key="temperature",
                    label="Operating temperature",
                    value=float(temp),
                    unit="°C",
                    max_threshold=80,
                    is_abnormal=temp > 80,
                )
            )
        insp = Inspection(
            id=new_id(),
            organization_id=org.id,
            asset_id=asset.id,
            template_id=template.id,
            inspector_id=who.id,
            reviewer_id=users["supervisor"].id if status in {InspectionStatus.REVIEWED.value, InspectionStatus.RESOLVED.value} else None,
            status=status,
            notes=notes,
            weather="Clear",
            started_at=created,
            submitted_at=created + timedelta(minutes=28),
            analyzed_at=created + timedelta(minutes=30),
            reviewed_at=created + timedelta(hours=6) if status in {InspectionStatus.REVIEWED.value, InspectionStatus.RESOLVED.value} else None,
            resolved_at=created + timedelta(days=2) if status == InspectionStatus.RESOLVED.value else None,
            duration_minutes=28,
            latitude=asset.latitude,
            longitude=asset.longitude,
            created_at=created,
            updated_at=created,
        )
        db.add(insp)
        await db.flush()
        for child in observations + measurements:
            child.inspection_id = insp.id
            db.add(child)
        result = calculate_risk(
            observations=[
                {"field_key": o.field_key, "category": o.category, "label": o.label, "value_text": o.value_text, "value_bool": o.value_bool}
                for o in observations
            ],
            measurements=[{"field_key": m.field_key, "label": m.label, "value": m.value, "unit": m.unit, "max_threshold": m.max_threshold} for m in measurements],
            previous_high_or_critical=1 if code == "T-104" else 0,
            measurement_thresholds=transformer_type.measurement_thresholds,
        )
        db.add(
            RiskAssessment(
                id=new_id(),
                inspection_id=insp.id,
                score=result.score,
                level=result.level.value,
                breakdown=result.breakdown,
                calculated_at=created + timedelta(minutes=29),
            )
        )
        db.add(
            AIAnalysis(
                id=new_id(),
                inspection_id=insp.id,
                status="completed",
                provider="heuristic",
                model="fieldops-heuristic-1.1",
                risk_summary=f"Historical inspection scored {result.level.value} ({result.score}/100). {notes}",
                possible_causes=["See captured evidence", "Compare with previous trend on this asset"],
                recommendations=["Supervisor review", "Continue monitoring if not critical"],
                supervisor_brief=notes,
                confidence=0.7,
                severity=result.level.value,
                used_fallback=True,
                latency_ms=8,
            )
        )
        asset.current_risk_score = result.score
        asset.current_risk_level = result.level.value
        asset.last_inspection_at = created

    # Open work orders
    db.add(
        WorkOrder(
            id=new_id(),
            organization_id=org.id,
            asset_id=assets["T-108"].id,
            title="Repair conservator bracket on T-108",
            description="High noise and visible structural damage. Assign a technician this week.",
            priority=WorkOrderPriority.HIGH.value,
            status=WorkOrderStatus.ASSIGNED.value,
            assigned_to=inspector2.id,
            created_by=users["supervisor"].id,
            due_at=now + timedelta(days=2),
        )
    )
    db.add(
        WorkOrder(
            id=new_id(),
            organization_id=org.id,
            asset_id=assets["PL-441"].id,
            title="Pole replacement assessment PL-441",
            description="Split pole reported. Verify before next storm cycle.",
            priority=WorkOrderPriority.MEDIUM.value,
            status=WorkOrderStatus.OPEN.value,
            created_by=users["supervisor"].id,
            due_at=now + timedelta(days=5),
        )
    )
    db.add(
        Notification(
            id=new_id(),
            organization_id=org.id,
            user_id=users["supervisor"].id,
            notification_type=NotificationType.SYSTEM.value,
            title="Welcome to FieldOps AI",
            body="Demo tenant is ready. Walk the T-104 inspection story from the map.",
            entity_type="asset",
            entity_id=assets["T-104"].id,
        )
    )
    db.add(
        Notification(
            id=new_id(),
            organization_id=org.id,
            user_id=inspector.id,
            notification_type=NotificationType.INSPECTION_REMINDER.value,
            title="T-104 is due for inspection",
            body="Midrand TX 4 has a climbing temperature trend. Complete a full transformer inspection.",
            entity_type="asset",
            entity_id=assets["T-104"].id,
        )
    )
