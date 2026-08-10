"""
Global exception handlers - the single place every error response gets
reshaped into one consistent envelope:

    {"error": {"code": "...", "message": "...", "details": ...}}

This deliberately does NOT require touching the 60+ `raise HTTPException(...)`
call sites throughout the app. FastAPI/Starlette dispatch every raised
exception to the most specific registered handler for its type, so
registering handlers here catches everything uniformly at one point.
"""

import logging

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

_STATUS_TO_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    502: "BAD_GATEWAY",
}


def _envelope(code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _STATUS_TO_CODE.get(exc.status_code, "ERROR")

    # Some of our own routes pass a dict as `detail` (e.g. Module 9's FHIR
    # export failure, which carries the full retry-attempt log) rather
    # than a plain string - preserve that structure as `details` instead
    # of collapsing it into a message string.
    if isinstance(exc.detail, dict):
        message = exc.detail.get("status", "Request failed")
        details = exc.detail
    else:
        message = str(exc.detail)
        details = None

    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        logger.warning(
            "Authentication failure", extra={"path": request.url.path, "method": request.method}
        )
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        logger.warning(
            "Authorization denied", extra={"path": request.url.path, "method": request.method}
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(code, message, details),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # exc.errors() can embed non-JSON-safe objects - e.g. a custom
    # @field_validator raising ValueError puts the actual exception
    # INSTANCE in ctx.error, not a string. FastAPI's default handler
    # papers over this with jsonable_encoder; a custom handler must too,
    # or plain json.dumps blows up on a real (if unusual) validation error.
    safe_errors = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=422,
        content=_envelope("VALIDATION_ERROR", "One or more fields are invalid", safe_errors),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    # Never leak raw DB error text (table/column/constraint names) to a
    # client - log the real exception server-side, return a generic message.
    logger.error(
        "Unhandled database error",
        extra={"path": request.url.path, "method": request.method},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500, content=_envelope("INTERNAL_ERROR", "A database error occurred")
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception",
        extra={"path": request.url.path, "method": request.method},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500, content=_envelope("INTERNAL_ERROR", "An unexpected error occurred")
    )
