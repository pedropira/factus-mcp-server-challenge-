"""Entry point for the Factus MCP Server.

Run with:  mcp run main.py
Dev mode:  mcp dev main.py
"""

from src.mcp_server.main import create_server

server = create_server()
