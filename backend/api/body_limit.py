"""ASGI middleware enforcing the 1 MiB request-body limit before any parsing.

Rejects early on an oversized Content-Length, otherwise buffers at most
``max_bytes`` (covers chunked bodies with no Content-Length) and replays the
buffered body to the application.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .errors import error_response


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    declared = -1
                if declared < 0:
                    await self._reject(scope, receive, send, 400, "INVALID_JSON", "Invalid Content-Length header.")
                    return
                if declared > self.max_bytes:
                    await self._too_large(scope, receive, send)
                    return

        chunks: list[bytes] = []
        size = 0
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.max_bytes:
                await self._too_large(scope, receive, send)
                return
            chunks.append(chunk)
            more = message.get("more_body", False)

        body = b"".join(chunks)
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

    async def _too_large(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self._reject(scope, receive, send, 413, "REQUEST_TOO_LARGE", "The request body exceeds 1 MiB.")

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send, status: int, code: str, message: str) -> None:
        response = error_response(status, code, message, headers={"Connection": "close"})
        await response(scope, receive, send)
