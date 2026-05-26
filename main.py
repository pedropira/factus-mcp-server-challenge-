"""Entry point for the Factus MCP Server.

Dev:        mcp dev main.py
Production: python main.py  (reads $PORT env var)

Uses Streamable HTTP transport so clients like OpenCode can
connect via a simple URL (e.g. https://example.com/mcp).
"""

import os

import uvicorn

from src.mcp_server.main import create_server

mcp = create_server()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        mcp.streamable_http_app(),
        host="0.0.0.0",
        port=port,
    )
