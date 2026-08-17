from app.engines.sync_engine import apply_push, conflict_status
from datetime import datetime, timedelta, timezone


def test_create_when_missing_server_record():
    result = apply_push("local-1", {"version": 1, "updated_at": datetime.now(timezone.utc)}, None)
    assert result["status"] == "synced"
    assert result["message"] == "created"


def test_conflict_when_versions_diverge():
    now = datetime.now(timezone.utc)
    status = conflict_status(1, 3, now, now + timedelta(minutes=2))
    assert status == "conflict"


def test_same_version_is_synced():
    now = datetime.now(timezone.utc)
    assert conflict_status(2, 2, now, now) == "synced"
