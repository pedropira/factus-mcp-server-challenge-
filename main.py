"""Entry point for the Factus MCP Server.

Dev:        mcp dev main.py
Production: python main.py  (reads $PORT env var)
"""

import os

from src.mcp_server.main import create_server

mcp = create_server()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=port,
    )
