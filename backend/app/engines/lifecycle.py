from app.exceptions import InvalidStateError
from app.models.entities import InspectionStatus

ALLOWED: dict[InspectionStatus, set[InspectionStatus]] = {
    InspectionStatus.DRAFT: {InspectionStatus.IN_PROGRESS, InspectionStatus.SUBMITTED},
    InspectionStatus.IN_PROGRESS: {InspectionStatus.DRAFT, InspectionStatus.SUBMITTED},
    InspectionStatus.SUBMITTED: {InspectionStatus.PROCESSING},
    InspectionStatus.PROCESSING: {InspectionStatus.ANALYZED, InspectionStatus.AI_FAILED},
    InspectionStatus.AI_FAILED: {InspectionStatus.PENDING_RETRY, InspectionStatus.ANALYZED, InspectionStatus.REVIEWED},
    InspectionStatus.PENDING_RETRY: {InspectionStatus.PROCESSING},
    InspectionStatus.ANALYZED: {InspectionStatus.REVIEWED, InspectionStatus.PENDING_RETRY},
    InspectionStatus.REVIEWED: {InspectionStatus.RESOLVED, InspectionStatus.ANALYZED},
    InspectionStatus.RESOLVED: set(),
}


class InspectionStateMachine:
    @staticmethod
    def parse(value: str) -> InspectionStatus:
        try:
            return InspectionStatus(value)
        except ValueError as exc:
            raise InvalidStateError(f"Unknown inspection status '{value}'") from exc

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        return cls.parse(target) in ALLOWED[cls.parse(current)]

    @classmethod
    def transition(cls, current: str, target: str) -> str:
        current_status = cls.parse(current)
        target_status = cls.parse(target)
        if target_status == current_status:
            return current_status.value
        if target_status not in ALLOWED[current_status]:
            raise InvalidStateError(
                f"Cannot move inspection from {current_status.value} to {target_status.value}",
                details={"from": current_status.value, "to": target_status.value},
            )
        return target_status.value

    @classmethod
    def is_editable(cls, status: str) -> bool:
        return cls.parse(status) in {InspectionStatus.DRAFT, InspectionStatus.IN_PROGRESS}

    @classmethod
    def is_terminal(cls, status: str) -> bool:
        return cls.parse(status) == InspectionStatus.RESOLVED
