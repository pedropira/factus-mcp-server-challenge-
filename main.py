"""Entry point for the Factus MCP Server.

Run with:  mcp run main.py
Dev mode:  mcp dev main.py
"""

import asyncio
from src.mcp_server.main import create_server

mcp = create_server()

async def main():
    async with mcp:
        pass


if __name__ == "__main__":
    asyncio.run(main())
