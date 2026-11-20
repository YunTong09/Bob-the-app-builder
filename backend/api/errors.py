"""Error envelope (docs/API_CONTRACT.md section 8) and exception handlers.

Every non-success response, including framework errors, goes through here.
Client-facing messages are fixed strings: they never echo request bodies,
drafts, provider responses, exception text or stack traces.
"""

from __future__ import annotations

import logging
from typing import Iterable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.application.errors import (
    MemoryIdConflictError,
    ModelError,
    ModelTimeoutError,
    OwnershipError,
    StorageUnavailableError,
)

log = logging.getLogger("rage_to_reply.api")

_MAX_FIELD_PATH = 120


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        details: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


def error_response(
    status: int,
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body, headers=headers)


def invalid_json() -> ApiError:
    return ApiError(400, "INVALID_JSON", "The request body is not valid JSON.")


def validation_error(details: list[dict[str, str]]) -> ApiError:
    return ApiError(422, "VALIDATION_ERROR", "Check the required fields.", details)


# ------------------------------------------------------------ pydantic mapping

_SAFE_MESSAGES = {
    "missing": "Field required.",
    "extra_forbidden": "Unknown field.",
    "string_type": "Must be a string.",
    "int_type": "Must be an integer.",
    "list_type": "Must be an array.",
    "model_type": "Must be an object.",
    "model_attributes_type": "Must be an object.",
    "dict_type": "Must be an object.",
    "literal_error": "Unsupported value.",
    "string_too_short": "Too short.",
    "string_too_long": "Too long.",
    "too_short": "Too few items.",
    "too_long": "Too many items.",
}


def _field_path(loc: Iterable[object]) -> str:
    path = ""
    for part in loc:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            # Skip Pydantic's internal union/function markers.
            text = str(part)
            if text.startswith(("function-", "union[")) or "[" in text and text.endswith("]"):
                continue
            path += ("." if path else "") + text
    if len(path) > _MAX_FIELD_PATH:
        path = path[:_MAX_FIELD_PATH] + "..."
    return path or "body"


def pydantic_details(exc: ValidationError) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    for err in exc.errors(include_input=False, include_url=False):
        err_type = err.get("type", "")
        if err_type == "value_error":
            # Our own validators raise ValueError with fixed, safe text.
            msg = str(err.get("ctx", {}).get("error", "Invalid value."))
        elif err_type in ("string_too_short", "string_too_long", "too_short", "too_long"):
            ctx = err.get("ctx", {})
            bound = ctx.get("min_length", ctx.get("max_length"))
            unit = "characters" if err_type.startswith("string") else "items"
            prefix = "At least" if "short" in err_type else "At most"
            msg = f"{prefix} {bound} {unit}." if bound is not None else _SAFE_MESSAGES[err_type]
        else:
            msg = _SAFE_MESSAGES.get(err_type, "Invalid value.")
        details.append({"field": _field_path(err.get("loc", ())), "message": msg})
    return details


# ------------------------------------------------------------ handlers

_STATUS_CODES = {
    404: ("NOT_FOUND", "No API route exists at this path."),
    405: ("METHOD_NOT_ALLOWED", "This route does not support the requested method."),
    413: ("REQUEST_TOO_LARGE", "The request body exceeds 1 MiB."),
    415: ("UNSUPPORTED_MEDIA_TYPE", "Send the request body as application/json."),
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.status, exc.code, exc.message, exc.details, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": _field_path(e.get("loc", ())[1:] or ("body",)), "message": _SAFE_MESSAGES.get(e.get("type", ""), "Invalid value.")}
            for e in exc.errors()
        ]
        return error_response(422, "VALIDATION_ERROR", "Check the required fields.", details)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, message = _STATUS_CODES.get(exc.status_code, ("INTERNAL_ERROR", "Unexpected server error."))
        status = exc.status_code if exc.status_code in _STATUS_CODES else 500
        return error_response(status, code, message, headers=getattr(exc, "headers", None))

    @app.exception_handler(MemoryIdConflictError)
    async def _conflict(_: Request, exc: MemoryIdConflictError) -> JSONResponse:
        return error_response(
            409,
            "MEMORY_ID_CONFLICT",
            "A message ID already exists with different details. Nothing was imported.",
        )

    @app.exception_handler(StorageUnavailableError)
    async def _storage(_: Request, exc: StorageUnavailableError) -> JSONResponse:
        log.warning("storage unavailable")
        return error_response(503, "SERVICE_UNAVAILABLE", "Conversation history storage is unavailable. Try again later.")

    @app.exception_handler(ModelTimeoutError)
    async def _timeout(_: Request, exc: ModelTimeoutError) -> JSONResponse:
        log.warning("model timeout")
        return error_response(504, "MODEL_TIMEOUT", "Reply generation timed out. Your input was not saved; try again.")

    @app.exception_handler(ModelError)
    async def _model(_: Request, exc: ModelError) -> JSONResponse:
        log.warning("model error: %s", type(exc).__name__)
        return error_response(502, "MODEL_ERROR", "A usable reply could not be generated. Try again.")

    @app.exception_handler(OwnershipError)
    async def _ownership(_: Request, exc: OwnershipError) -> JSONResponse:
        log.error("ownership could not be enforced")
        return error_response(500, "INTERNAL_ERROR", "Unexpected server error.")

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        # Log the type only; exception text could contain user content.
        log.error("unexpected error: %s", type(exc).__name__)
        return error_response(500, "INTERNAL_ERROR", "Unexpected server error.")
