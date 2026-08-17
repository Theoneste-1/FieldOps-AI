from datetime import datetime, timezone
from typing import Any

from app.models.entities import SyncStatus


def conflict_status(client_version: int, server_version: int, client_updated: datetime, server_updated: datetime) -> str:
    """Optimistic concurrency with an explicit conflict state.

    Last-write-wins is used only when versions match. Divergent versions become CONFLICT
    so the client can present a resolution UI instead of silently dropping field data.
    """
    if client_version == server_version:
        return SyncStatus.SYNCED.value
    if client_updated > server_updated and client_version > server_version:
        return SyncStatus.SYNCED.value
    return SyncStatus.CONFLICT.value


def apply_push(local_id: str, payload: dict[str, Any], server_record: dict[str, Any] | None) -> dict[str, Any]:
    result = {
        "local_id": local_id,
        "status": SyncStatus.SYNCED.value,
        "message": None,
        "server_id": None,
        "server_version": 1,
    }
    if server_record is None:
        result["message"] = "created"
        return result

    status = conflict_status(
        client_version=int(payload.get("version", 1)),
        server_version=int(server_record.get("version", 1)),
        client_updated=_as_dt(payload.get("updated_at")),
        server_updated=_as_dt(server_record.get("updated_at")),
    )
    result["status"] = status
    result["server_id"] = server_record.get("id")
    result["server_version"] = server_record.get("version", 1)
    if status == SyncStatus.CONFLICT.value:
        result["message"] = "Server copy is newer or diverged; resolve on device"
    else:
        result["message"] = "updated"
    return result


def _as_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)
