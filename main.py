"""Entry point for the Factus MCP Server.

Dev:        mcp dev main.py
Production: python main.py  (reads $PORT env var)
"""

import os

import uvicorn

from src.mcp_server.main import create_server

mcp = create_server()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        mcp.sse_app(),
        host="0.0.0.0",
        port=port,
    )
