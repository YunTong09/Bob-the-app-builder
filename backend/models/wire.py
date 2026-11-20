"""HTTP wire models. Source of truth: docs/API_CONTRACT.md (do not diverge).

All models are strict (no coercion), reject unknown fields and use camelCase
aliases on the wire.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
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
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt]"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]+)?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
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
    # datetime.fromisoformat can normalize invalid components, such as +00:99
    # (and 24:00 on newer Python versions), so check their ranges first.
    if not _RFC3339.fullmatch(v):
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


# ---------------------------------------------------------- Slack preview


def _slack_channel(v: str) -> str:
    if not re.fullmatch(r"[CG][A-Z0-9]{1,127}", v):
        raise ValueError("Must be a public or private Slack channel ID.")
    return v


def _slack_cursor(v: str) -> str:
    if not v or any(ord(character) < 33 or ord(character) > 126 for character in v):
        raise ValueError("Must be a printable ASCII cursor without whitespace.")
    return v


def _slack_bound(v: str) -> str:
    fraction = re.search(r"\.([0-9]+)(?:[Zz]|[+-][0-9]{2}:[0-9]{2})$", v)
    if fraction and any(digit != "0" for digit in fraction.group(1)[6:]):
        raise ValueError("Use at most six meaningful fractional-second digits.")
    try:
        when = datetime.fromisoformat(v.replace("z", "Z").replace("t", "T").replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise ValueError("Must be a representable UTC date-time.") from None
    if when < datetime(1970, 1, 1, tzinfo=timezone.utc):
        raise ValueError("Must be on or after the Unix epoch.")
    return v


SlackChannelId = Annotated[str, AfterValidator(_slack_channel)]
SlackCursor = Annotated[str, Field(min_length=1, max_length=2048), AfterValidator(_slack_cursor)]
SlackDateBound = Annotated[Timestamp, AfterValidator(_slack_bound)]


class SlackPreviewRequest(_Request):
    channel_id: SlackChannelId
    oldest: SlackDateBound | None = None
    latest: SlackDateBound | None = None
    cursor: SlackCursor | None = None
    limit: int = Field(default=100, ge=1, le=100)

    @field_validator("oldest", "latest", "cursor", mode="before")
    @classmethod
    def _no_explicit_null(cls, v: object) -> object:
        if v is None:
            raise ValueError("Omit unknown fields instead of sending null.")
        return v

    @model_validator(mode="after")
    def _ordered_window(self) -> SlackPreviewRequest:
        if self.oldest is not None and self.latest is not None:
            oldest = datetime.fromisoformat(self.oldest.replace("z", "Z").replace("t", "T").replace("Z", "+00:00"))
            latest = datetime.fromisoformat(self.latest.replace("z", "Z").replace("t", "T").replace("Z", "+00:00"))
            if oldest > latest:
                raise ValueError("oldest must not be later than latest.")
        return self


class SlackPreviewResponse(_Response):
    messages: list[MemoryMessage] = Field(max_length=100)
    next_cursor: SlackCursor | None
    skipped_count: int = Field(ge=0)
    warnings: list[str]


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
