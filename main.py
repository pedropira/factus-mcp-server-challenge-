"""Entry point for the Factus MCP Server.

Dev:        mcp dev main.py
Production: python main.py  (reads $PORT env var)

Uses Streamable HTTP transport so clients like OpenCode can
connect via a simple URL (e.g. https://example.com/mcp).
"""

import logging
import os

import uvicorn
from starlette.applications import Starlette
from starlette.types import Receive, Scope, Send

from src.mcp_server.main import create_server

# ── Session lifecycle debug ──────────────────────────────────────────────
# Enable DEBUG logging for MCP session manager to see session creation,
# reuse, and cleanup in Render logs.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("mcp.server.streamable_http_manager").setLevel(logging.DEBUG)
logging.getLogger("mcp.server.streamable_http").setLevel(logging.DEBUG)

session_logger = logging.getLogger("mcp.session_lifecycle")


class SessionLoggingMiddleware:
    """ASGI middleware that logs session lifecycle events.

    Wraps the StreamableHTTP session manager's handle_request to log
    exactly when sessions are created, found, or not found — without
    modifying the SDK.
    """

    def __init__(self, app: Starlette):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Intercept the response to extract mcp-session-id header
        original_send = send

        async def intercepted_send(message):
            if message["type"] == "http.response.start":
                # Log session info from status
                status = message.get("status", 0)
                headers = dict(message.get("headers", []))
                session_id = headers.get(b"mcp-session-id", b"").decode() if b"mcp-session-id" in headers else None
                if session_id:
                    if status == 200:
                        session_logger.info("SESSION OK | id=%s | status=%s", session_id, status)
                    elif status == 404:
                        session_logger.warning("SESSION NOT FOUND | id=%s | status=%s", session_id, status)
                    else:
                        session_logger.info("SESSION REQUEST | id=%s | status=%s", session_id, status)
                else:
                    # New session creation
                    if status == 200:
                        session_logger.info("SESSION CREATED | no-id-in-request | status=%s", status)
            await original_send(message)

        await self.app(scope, receive, intercepted_send)


mcp = create_server()

# Access the session manager to wrap it with logging
# FastMCP creates the session manager lazily on first call to streamable_http_app()
session_logger.info("Initializing MCP server with session debugging...")
starlette_app = mcp.streamable_http_app()

# Wrap with session logging middleware
wrapped_app = SessionLoggingMiddleware(starlette_app)

# Log session manager details
if mcp._session_manager is not None:  # type: ignore[attr-defined]  # noqa: SLF001
    sm = mcp._session_manager  # type: ignore[attr-defined]  # noqa: SLF001
    session_logger.info(
        "Session manager: json_response=%s, stateless=%s, idle_timeout=%s, type=%s",
        getattr(sm, "json_response", "?"),
        getattr(sm, "stateless", "?"),
        getattr(sm, "session_idle_timeout", "?"),
        type(sm).__name__,
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        wrapped_app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
    )
