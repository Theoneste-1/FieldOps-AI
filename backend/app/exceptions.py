from fastapi import HTTPException, status


class FieldOpsError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message, "details": details or {}},
        )
        self.code = code


class UnauthorizedError(FieldOpsError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "unauthorized", message)


class ForbiddenError(FieldOpsError):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(status.HTTP_403_FORBIDDEN, "forbidden", message)


class NotFoundError(FieldOpsError):
    def __init__(self, entity: str, identifier: str | None = None):
        message = f"{entity} not found" if not identifier else f"{entity} '{identifier}' not found"
        super().__init__(status.HTTP_404_NOT_FOUND, "not_found", message)


class ConflictError(FieldOpsError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(status.HTTP_409_CONFLICT, "conflict", message, details)


class ValidationAppError(FieldOpsError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, "validation_error", message, details)


class InvalidStateError(FieldOpsError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(status.HTTP_409_CONFLICT, "invalid_state", message, details)
