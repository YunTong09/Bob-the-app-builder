"""HTTP wire models. Source of truth: docs/API_CONTRACT.md (do not diverge).

All models are strict (no coercion), reject unknown fields and use camelCase
aliases on the wire.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from pydantic.alias_generators import to_camel

MAX_BODY_BYTES = 1_048_576
ID_MAX = 128
TEXT_MAX = 10_000
LABEL_MAX = 200
QUERY_MAX = 500
IMPORT_MIN, IMPORT_MAX = 1, 100
SEARCH_LIMIT_MIN, SEARCH_LIMIT_MAX, SEARCH_LIMIT_DEFAULT = 1, 100, 20

ReplyTone = Literal["diplomatic", "neutral", "assertive"]

# RFC 3339 date-time with mandatory timezone (Z or +/-HH:MM).
_RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$"
)


def _non_blank(v: str) -> str:
    if not v.strip():
        raise ValueError("Must contain a non-whitespace character.")
    return v


def _identifier(v: str) -> str:
    if v != v.strip():
        raise ValueError("Must not have leading or trailing whitespace.")
    return _non_blank(v)


def _rfc3339(v: str) -> str:
    if not _RFC3339.match(v):
        raise ValueError("Must be an RFC 3339 date-time with an explicit timezone.")
    try:
        datetime.fromisoformat(v.replace("z", "Z").replace("t", "T").replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Must be an RFC 3339 date-time with an explicit timezone.") from None
    return v  # stored verbatim, never rewritten


Identifier = Annotated[str, Field(min_length=1, max_length=ID_MAX), AfterValidator(_identifier)]
MessageText = Annotated[str, Field(min_length=1, max_length=TEXT_MAX), AfterValidator(_non_blank)]
Label = Annotated[str, Field(min_length=1, max_length=LABEL_MAX), AfterValidator(_non_blank)]
Timestamp = Annotated[str, AfterValidator(_rfc3339)]


class _Request(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=False,
        frozen=True,
    )


class _Response(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
    )


# ---------------------------------------------------------------- generation


class GenerateReplyRequest(_Request):
    manager_message: MessageText
    employee_draft: MessageText
    tone: ReplyTone
    conversation_id: Identifier | None = None

    @field_validator("conversation_id", mode="before")
    @classmethod
    def _no_explicit_null(cls, v: object) -> object:
        if v is None:
            raise ValueError("Omit this field instead of sending null.")
        return v


class Evidence(_Response):
    message_id: str
    content: str
    sender: str
    timestamp: str | None
    supported_claim: str
    source: str | None = None


class GenerateReplyResponse(_Response):
    reply: str
    manager_intent: str
    employee_concern: str
    evidence: list[Evidence]
    unverified_claims: list[str]
    warnings: list[str]


# ---------------------------------------------------------------- memory


class MemoryMessage(_Request):
    id: Identifier
    conversation_id: Identifier
    sender: Label
    content: MessageText
    # Optional, but explicit null is rejected (contract: omit unknown metadata).
    timestamp: Timestamp | None = None
    source: Label | None = None

    @field_validator("timestamp", "source", mode="before")
    @classmethod
    def _no_explicit_null(cls, v: object) -> object:
        if v is None:
            raise ValueError("Omit unknown metadata instead of sending null.")
        return v


class ImportMemoryRequest(_Request):
    messages: Annotated[list[MemoryMessage], Field(min_length=IMPORT_MIN, max_length=IMPORT_MAX)]


class ImportMemoryResponse(_Response):
    imported_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)


class StoredMemoryMessage(_Response):
    id: str
    conversation_id: str
    sender: str
    content: str
    timestamp: str | None
    source: str | None


class SearchMemoryResponse(_Response):
    messages: list[StoredMemoryMessage]
    total: int = Field(ge=0)
    limit: int = Field(ge=SEARCH_LIMIT_MIN, le=SEARCH_LIMIT_MAX)
    offset: int = Field(ge=0)


class DeleteMemoryResponse(_Response):
    deleted_count: int = Field(ge=0)


# ---------------------------------------------------------------- errors


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ApiErrorResponse(BaseModel):
    error: ErrorBody
