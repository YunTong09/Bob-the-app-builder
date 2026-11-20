"""FastAPI application: P0 routes from docs/API_CONTRACT.md.

Routes are thin: derive owner -> validate wire input -> call the HTTP-free
``RageToReplyApp`` -> convert to wire response. Request bodies are parsed
manually so that content type, JSON syntax and schema failures map exactly to
415 / 400 / 422 in the contract's error envelope.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ValidationError

from backend.application.orchestrator import RageToReplyApp
from backend.application.ports import MemoryRecord, OwnerContext, Services
from backend.models.wire import (
    MAX_BODY_BYTES,
    QUERY_MAX,
    SEARCH_LIMIT_DEFAULT,
    SEARCH_LIMIT_MAX,
    SEARCH_LIMIT_MIN,
    DeleteMemoryResponse,
    Evidence,
    GenerateReplyRequest,
    GenerateReplyResponse,
    ImportMemoryRequest,
    ImportMemoryResponse,
    SearchMemoryResponse,
    StoredMemoryMessage,
    _identifier,
)

from .body_limit import BodyLimitMiddleware
from .errors import ApiError, install_error_handlers, invalid_json, pydantic_details, validation_error
from .identity import IdentityResolver

log = logging.getLogger("rage_to_reply.api")

M = TypeVar("M", bound=BaseModel)


# ------------------------------------------------------------------ helpers


def _require_json_content_type(request: Request) -> None:
    raw = request.headers.get("content-type")
    if raw is None:
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Send the request body as application/json.")
    media, *params = [p.strip() for p in raw.split(";")]
    charset_ok = all(
        not p.lower().startswith("charset=") or p.split("=", 1)[1].strip('"').lower() in ("utf-8", "utf8")
        for p in params
    )
    if media.lower() != "application/json" or not charset_ok:
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Send the request body as application/json.")


def _reject_constant(_: str) -> Any:
    raise ValueError("non-standard JSON constant")


async def _parse_body(request: Request, model: type[M]) -> M:
    _require_json_content_type(request)
    raw = await request.body()  # already capped by BodyLimitMiddleware
    try:
        data = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, ValueError):
        raise invalid_json() from None
    if not isinstance(data, dict):
        raise validation_error([{"field": "body", "message": "Must be a JSON object."}])
    try:
        return model.model_validate(data, by_alias=True, by_name=False)
    except ValidationError as exc:
        raise validation_error(pydantic_details(exc)) from None


def _reject_query_params(request: Request, allowed: set[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    errors = []
    for key, value in request.query_params.multi_items():
        if key not in allowed:
            errors.append({"field": key[:64], "message": "Unknown query parameter."})
        elif key in params:
            errors.append({"field": key, "message": "Supply this parameter at most once."})
        else:
            params[key] = value
    if errors:
        raise validation_error(errors)
    return params


async def _reject_body(request: Request) -> None:
    if await request.body():
        raise validation_error([{"field": "body", "message": "This request does not accept a body."}])


def _parse_int(value: str | None, field: str, default: int, lo: int, hi: int | None) -> int:
    if value is None:
        return default
    if not value.isascii() or not value.isdigit():
        raise validation_error([{"field": field, "message": "Must be an integer."}])
    n = int(value)
    if n < lo or (hi is not None and n > hi):
        bound = f"between {lo} and {hi}" if hi is not None else f"at least {lo}"
        raise validation_error([{"field": field, "message": f"Must be {bound}."}])
    return n


# ------------------------------------------------------------------ factory


def create_app(services: Services, identity: IdentityResolver) -> FastAPI:
    app_service = RageToReplyApp(services)
    app = FastAPI(
        title="Rage-to-Reply API",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    install_error_handlers(app)
    app.add_middleware(BodyLimitMiddleware, max_bytes=MAX_BODY_BYTES)

    def owner_of(request: Request) -> OwnerContext:
        owner = identity(request)
        if not isinstance(owner, OwnerContext):
            raise ApiError(401, "UNAUTHENTICATED", "Authentication is required.")
        return owner

    # ---------------------------------------------------------- generation
    @app.post("/api/reply/generate")
    async def generate(request: Request) -> GenerateReplyResponse:
        owner = owner_of(request)
        _reject_query_params(request, set())
        body = await _parse_body(request, GenerateReplyRequest)
        result = await run_in_threadpool(
            app_service.generate_reply,
            owner,
            manager_message=body.manager_message,
            employee_draft=body.employee_draft,
            tone=body.tone,
            conversation_id=body.conversation_id,
        )
        return GenerateReplyResponse(
            reply=result.reply,
            manager_intent=result.manager_intent,
            employee_concern=result.employee_concern,
            evidence=[
                Evidence(
                    message_id=e.message_id,
                    content=e.content,
                    sender=e.sender,
                    timestamp=e.timestamp,
                    supported_claim=e.supported_claim,
                    source=e.source,
                )
                for e in result.evidence
            ],
            unverified_claims=list(result.unverified_claims),
            warnings=list(result.warnings),
        )

    # ---------------------------------------------------------- memory
    @app.post("/api/memory/import")
    async def import_memory(request: Request) -> ImportMemoryResponse:
        owner = owner_of(request)
        _reject_query_params(request, set())
        body = await _parse_body(request, ImportMemoryRequest)

        seen: dict[str, int] = {}
        dupes = []
        for i, m in enumerate(body.messages):
            if m.id in seen:
                dupes.append({"field": f"messages[{i}].id", "message": "Duplicate ID in this request."})
            seen.setdefault(m.id, i)
        if dupes:
            raise validation_error(dupes)

        records = [
            MemoryRecord(
                id=m.id,
                conversation_id=m.conversation_id,
                sender=m.sender,
                content=m.content,
                timestamp=m.timestamp,
                source=m.source,
            )
            for m in body.messages
        ]
        imported, skipped = await run_in_threadpool(app_service.import_memory, owner, records)
        return ImportMemoryResponse(imported_count=imported, skipped_count=skipped)

    @app.get("/api/memory/search")
    async def search_memory(request: Request) -> SearchMemoryResponse:
        owner = owner_of(request)
        params = _reject_query_params(request, {"q", "conversationId", "limit", "offset"})

        q = params.get("q")
        if q is not None and len(q) > QUERY_MAX:
            raise validation_error([{"field": "q", "message": f"At most {QUERY_MAX} characters."}])
        query = q if q is not None and q.strip() else None

        conversation_id = params.get("conversationId")
        if conversation_id is not None:
            try:
                if not 1 <= len(conversation_id) <= 128:
                    raise ValueError("Must contain 1-128 characters.")
                _identifier(conversation_id)
            except ValueError as exc:
                raise validation_error([{"field": "conversationId", "message": str(exc)}]) from None

        limit = _parse_int(params.get("limit"), "limit", SEARCH_LIMIT_DEFAULT, SEARCH_LIMIT_MIN, SEARCH_LIMIT_MAX)
        offset = _parse_int(params.get("offset"), "offset", 0, 0, None)

        page = await run_in_threadpool(
            app_service.search_memory,
            owner,
            query=query,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )
        return SearchMemoryResponse(
            messages=[
                StoredMemoryMessage(
                    id=r.id,
                    conversation_id=r.conversation_id,
                    sender=r.sender,
                    content=r.content,
                    timestamp=r.timestamp,
                    source=r.source,
                )
                for r in page.records
            ],
            total=page.total,
            limit=limit,
            offset=offset,
        )

    @app.delete("/api/memory")
    async def delete_memory(request: Request) -> DeleteMemoryResponse:
        owner = owner_of(request)
        _reject_query_params(request, set())
        await _reject_body(request)
        deleted = await run_in_threadpool(app_service.delete_memory, owner)
        return DeleteMemoryResponse(deleted_count=deleted)

    # ---------------------------------------------------------- P1 (deferred)
    @app.api_route("/api/preferences", methods=["GET", "PUT"])
    async def preferences(_: Request) -> None:
        raise ApiError(501, "NOT_IMPLEMENTED", "Communication preferences are not available yet.")

    return app
