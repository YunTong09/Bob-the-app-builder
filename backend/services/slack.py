"""Read-only, single-channel Slack preview for the restricted web demo.

Only explicit preview calls contact Slack. This module never stores messages,
calls a model, resolves display names, follows links, or writes to Slack.
"""

from __future__ import annotations

import json
import os
import re
import time
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from backend.application.errors import SlackImportError
from backend.application.ports import MemoryRecord


SLACK_API = "https://slack.com/api/"
MAX_RESPONSE_BYTES = 1_048_576
REQUEST_TIMEOUT_SECONDS = 10.0
MAX_CURSOR_CHARS = 2048

_CHANNEL_ID = re.compile(r"[CG][A-Z0-9]{1,127}")
_TEAM_ID = re.compile(r"T[A-Z0-9]{1,127}")
_USER_ID = re.compile(r"[UW][A-Z0-9]{1,199}")
_BOT_ID = re.compile(r"B[A-Z0-9]{1,199}")
_BOT_TOKEN = re.compile(r"xoxb-[A-Za-z0-9-]+")
_SLACK_TS = re.compile(r"(0|[1-9][0-9]{0,11})\.([0-9]{6})")
_BOUND = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt](?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.([0-9]+))?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

WARNING_TEXT_ONLY = "Only channel-level message text is previewed; files and thread replies are not fetched."
WARNING_SKIPPED = "Some Slack entries were skipped because their type, content or metadata is unsupported."


@dataclass(frozen=True)
class SlackPreviewPage:
    messages: tuple[MemoryRecord, ...]
    next_cursor: str | None
    skipped_count: int
    warnings: tuple[str, ...]


def _retry_after(value: str | None) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value):
        return 60
    significant = value.lstrip("0")
    if len(significant) > 4:
        return 3600
    return max(1, min(int(significant or "0"), 3600))


def _cursor(value: object) -> str | None:
    if value is None or value == "":
        return None
    if (
        not isinstance(value, str)
        or len(value) > MAX_CURSOR_CHARS
        or value != value.strip()
        or any(ord(character) < 33 or ord(character) > 126 for character in value)
    ):
        raise ValueError("Invalid Slack cursor.")
    return value


def _epoch_timestamp(value: str | None) -> str | None:
    if value is None:
        return None
    match = _BOUND.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise ValueError("Invalid Slack date bound.")
    fraction = match.group(1) or ""
    # Slack timestamps have microsecond precision. Never silently discard a
    # meaningful sub-microsecond component supplied in an RFC 3339 bound.
    if len(fraction) > 6 and any(character != "0" for character in fraction[6:]):
        raise ValueError("Slack date bounds require microsecond precision.")
    try:
        parsed = datetime.fromisoformat(value.replace("t", "T").replace("z", "Z").replace("Z", "+00:00"))
        delta = parsed.astimezone(timezone.utc) - _EPOCH
    except (ValueError, OverflowError):
        raise ValueError("Invalid Slack date bound.") from None
    if delta.days < 0:
        raise ValueError("Slack date bounds must not precede the Unix epoch.")
    seconds = delta.days * 86400 + delta.seconds
    return f"{seconds}.{delta.microseconds:06d}"


def _message_timestamp(value: object) -> str | None:
    match = _SLACK_TS.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return None
    try:
        parsed = _EPOCH + timedelta(seconds=int(match.group(1)), microseconds=int(match.group(2)))
    except (ValueError, OverflowError):
        return None
    return parsed.isoformat(timespec="microseconds")


def _provider_error(code: object, retry_header: str | None) -> SlackImportError:
    if code in ("invalid_auth", "not_authed", "token_revoked", "account_inactive", "not_allowed_token_type"):
        return SlackImportError("SLACK_AUTH_FAILED")
    if code in ("missing_scope", "no_permission", "not_in_channel", "restricted_action", "access_denied"):
        return SlackImportError("SLACK_PERMISSION_DENIED")
    if code == "channel_not_found":
        return SlackImportError("SLACK_CHANNEL_NOT_FOUND")
    if code in ("ratelimited", "rate_limited"):
        return SlackImportError("SLACK_RATE_LIMITED", retry_after=_retry_after(retry_header))
    if code in ("internal_error", "fatal_error", "service_unavailable", "request_timeout"):
        return SlackImportError("SLACK_UNAVAILABLE")
    return SlackImportError("SLACK_UPSTREAM_ERROR")


class SlackHistoryService:
    def __init__(self, token: str, channel_id: str, *, client: httpx.Client | None = None) -> None:
        if (
            not isinstance(token, str)
            or _BOT_TOKEN.fullmatch(token) is None
            or not isinstance(channel_id, str)
            or _CHANNEL_ID.fullmatch(channel_id) is None
        ):
            raise ValueError("Invalid Slack demo configuration.")
        self._token = token
        self._channel_id = channel_id
        self._client = client

    def preview(
        self,
        *,
        channel_id: str,
        oldest: str | None = None,
        latest: str | None = None,
        cursor: str | None = None,
        limit: int = 100,
    ) -> SlackPreviewPage:
        # Check the server allowlist before even testing credentials upstream.
        if channel_id != self._channel_id:
            raise SlackImportError("SLACK_CHANNEL_NOT_ALLOWED")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Slack preview limit must be between 1 and 100.")
        oldest_ts, latest_ts = _epoch_timestamp(oldest), _epoch_timestamp(latest)
        if oldest_ts is not None and latest_ts is not None:
            oldest_parts = tuple(int(part) for part in oldest_ts.split("."))
            latest_parts = tuple(int(part) for part in latest_ts.split("."))
            if oldest_parts > latest_parts:
                raise ValueError("Slack date bounds are reversed.")
        next_cursor = _cursor(cursor)
        params: dict[str, str | int] = {"channel": self._channel_id, "limit": limit}
        if oldest_ts is not None:
            params["oldest"] = oldest_ts
        if latest_ts is not None:
            params["latest"] = latest_ts
        if oldest_ts is not None or latest_ts is not None:
            params["inclusive"] = "true"
        if next_cursor is not None:
            params["cursor"] = next_cursor

        managed_client = nullcontext(self._client) if self._client is not None else httpx.Client(trust_env=False)
        with managed_client as client:
            identity = self._call(client, "POST", "auth.test", {})
            team_id = identity.get("team_id")
            if not isinstance(team_id, str) or _TEAM_ID.fullmatch(team_id) is None:
                raise SlackImportError("SLACK_UPSTREAM_ERROR")
            page = self._call(client, "GET", "conversations.history", params)
        return self._normalise(page, team_id, limit)

    def _call(self, client: httpx.Client, verb: str, method: str, params: dict[str, str | int]) -> dict[str, Any]:
        deadline = time.monotonic() + REQUEST_TIMEOUT_SECONDS
        try:
            with client.stream(
                verb,
                SLACK_API + method,
                params=params,
                headers={"Authorization": f"Bearer {self._token}", "Accept": "application/json"},
                auth=None,
                timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS, connect=5.0),
                follow_redirects=False,
            ) as response:
                if response.status_code == 429:
                    raise SlackImportError("SLACK_RATE_LIMITED", retry_after=_retry_after(response.headers.get("Retry-After")))
                if response.status_code == 401:
                    raise SlackImportError("SLACK_AUTH_FAILED")
                if response.status_code == 403:
                    raise SlackImportError("SLACK_PERMISSION_DENIED")
                if response.status_code >= 500:
                    raise SlackImportError("SLACK_UNAVAILABLE")
                if response.status_code != 200:
                    raise SlackImportError("SLACK_UPSTREAM_ERROR")
                length = response.headers.get("Content-Length")
                if length and length.isascii() and length.isdigit():
                    if len(length) > 8 or int(length) > MAX_RESPONSE_BYTES:
                        raise SlackImportError("SLACK_UPSTREAM_ERROR")
                content = bytearray()
                for chunk in response.iter_bytes():
                    if time.monotonic() > deadline:
                        raise SlackImportError("SLACK_TIMEOUT")
                    if len(content) + len(chunk) > MAX_RESPONSE_BYTES:
                        raise SlackImportError("SLACK_UPSTREAM_ERROR")
                    content.extend(chunk)
                try:
                    data = json.loads(content)
                except (ValueError, UnicodeError, RecursionError):
                    raise SlackImportError("SLACK_UPSTREAM_ERROR") from None
                if not isinstance(data, dict) or type(data.get("ok")) is not bool:
                    raise SlackImportError("SLACK_UPSTREAM_ERROR")
                if not data["ok"]:
                    raise _provider_error(data.get("error"), response.headers.get("Retry-After"))
                return data
        except httpx.TimeoutException:
            raise SlackImportError("SLACK_TIMEOUT") from None
        except httpx.RequestError:
            raise SlackImportError("SLACK_UNAVAILABLE") from None

    def _normalise(self, page: dict[str, Any], team_id: str, limit: int) -> SlackPreviewPage:
        raw_messages = page.get("messages")
        if not isinstance(raw_messages, list) or len(raw_messages) > limit:
            raise SlackImportError("SLACK_UPSTREAM_ERROR")
        metadata = page.get("response_metadata", {})
        if not isinstance(metadata, dict):
            raise SlackImportError("SLACK_UPSTREAM_ERROR")
        try:
            cursor = _cursor(metadata.get("next_cursor"))
        except ValueError:
            raise SlackImportError("SLACK_UPSTREAM_ERROR") from None
        has_more = page.get("has_more", False)
        if type(has_more) is not bool:
            raise SlackImportError("SLACK_UPSTREAM_ERROR")
        if has_more and cursor is None:
            raise SlackImportError("SLACK_UPSTREAM_ERROR")
        records: list[MemoryRecord] = []
        seen: set[str] = set()
        skipped = 0
        for raw in raw_messages:
            record = self._normalise_message(raw, team_id)
            if record is None or record.id in seen:
                skipped += 1
                continue
            records.append(record)
            seen.add(record.id)
        warnings = [WARNING_TEXT_ONLY]
        if skipped:
            warnings.append(WARNING_SKIPPED)
        return SlackPreviewPage(tuple(records), cursor, skipped, tuple(warnings))

    def _normalise_message(self, raw: object, team_id: str) -> MemoryRecord | None:
        if (
            not isinstance(raw, dict)
            or raw.get("type") != "message"
            or raw.get("subtype") not in (None, "bot_message")
            or raw.get("hidden", False) is not False
            or raw.get("channel", self._channel_id) != self._channel_id
        ):
            return None
        text, ts = raw.get("text"), raw.get("ts")
        if not isinstance(text, str) or not 1 <= len(text) <= 10_000 or not text.strip():
            return None
        try:
            text.encode("utf-8")
        except UnicodeEncodeError:
            return None  # escaped lone surrogates cannot be returned as UTF-8 JSON
        timestamp = _message_timestamp(ts)
        if timestamp is None or raw.get("thread_ts", ts) != ts:
            return None
        user, bot = raw.get("user"), raw.get("bot_id")
        if isinstance(user, str) and _USER_ID.fullmatch(user):
            sender = user
        elif user is None and isinstance(bot, str) and _BOT_ID.fullmatch(bot):
            sender = bot
        else:
            return None
        record_id = f"slack:{team_id}:{self._channel_id}:{ts}"
        conversation_id = f"slack:{team_id}:{self._channel_id}"
        source = f"Slack {team_id}/{self._channel_id}/{ts}"
        if len(record_id) > 128 or len(conversation_id) > 128 or len(source) > 200:
            return None
        return MemoryRecord(record_id, conversation_id, sender, text, timestamp, source)


def build_slack_service() -> SlackHistoryService | None:
    """Configuration-only builder: absent/invalid settings disable the preview."""
    try:
        return SlackHistoryService(os.environ.get("SLACK_BOT_TOKEN", ""), os.environ.get("R2R_SLACK_CHANNEL_ID", ""))
    except (TypeError, ValueError):
        return None
