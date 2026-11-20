"""Failure types shared by the application layer and Developer 3's services.

Messages passed to these exceptions are for internal diagnostics only; the API
layer never returns them to clients (it uses fixed, safe messages instead), so
they must still never contain drafts, prompts, credentials or provider output.
"""

from __future__ import annotations


class ApplicationError(Exception):
    """Base class for expected service failures."""


class OwnershipError(ApplicationError):
    """Ownership could not be established or enforced. Never a reason to fall
    back to unscoped retrieval."""


class StorageUnavailableError(ApplicationError):
    """Memory storage is unavailable (HTTP 503, or warned fallback during
    generation once ownership is established)."""


class MemoryIdConflictError(ApplicationError):
    """An imported ID exists for this owner with different fields (HTTP 409)."""

    def __init__(self, conflicting_ids: tuple[str, ...] = ()) -> None:
        super().__init__("memory id conflict")
        self.conflicting_ids = conflicting_ids


class ModelError(ApplicationError):
    """Claude failed or returned unusable output (HTTP 502)."""


class EvidenceValidationError(ModelError):
    """The draft failed evidence validation and cannot be returned (HTTP 502)."""


class ModelTimeoutError(ApplicationError):
    """Claude exceeded the configured timeout (HTTP 504)."""
