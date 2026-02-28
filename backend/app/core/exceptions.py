import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import correlation_id_ctx

logger = logging.getLogger(__name__)


class SRIPBaseException(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "SRIP_ERROR"

    def __init__(self, message: str, details: Any = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        if status_code is not None:
            self.status_code = status_code


class NotFoundException(SRIPBaseException):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"


class DuplicateException(SRIPBaseException):
    status_code = status.HTTP_409_CONFLICT
    code = "DUPLICATE_RESOURCE"


class AuthorizationException(SRIPBaseException):
    status_code = status.HTTP_403_FORBIDDEN
    code = "AUTHORIZATION_FAILED"


class ValidationException(SRIPBaseException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "VALIDATION_FAILED"


class ExternalServiceException(SRIPBaseException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "EXTERNAL_SERVICE_FAILURE"


def error_envelope(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "correlation_id": correlation_id_ctx.get(),
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SRIPBaseException)
    async def srip_exception_handler(_: Request, exc: SRIPBaseException) -> JSONResponse:
        logger.error(exc.message, extra={"extra": {"code": exc.code}})
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{"field": ".".join(map(str, e["loc"])), "msg": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_envelope("REQUEST_VALIDATION_ERROR", "Request validation failed.", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope("HTTP_ERROR", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.critical("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_envelope("INTERNAL_SERVER_ERROR", "An unexpected error occurred."),
        )
