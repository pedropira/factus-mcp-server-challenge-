---
name: mcp-server-python
description: >
  MCP (Model Context Protocol) server patterns for Python, including tool registration, parameter schemas, server lifecycle, and transport configuration.
  Trigger: When creating MCP servers, registering tools, defining tool schemas, or building MCP-based integrations in Python.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Building an MCP server in Python using the `mcp` library
- Registering tools with input validation via Pydantic
- Defining tool parameter schemas with JSON Schema
- Configuring server transport (stdio, SSE) for different deployment modes
- Handling tool execution errors and returning structured responses
- Integrating external APIs or databases as MCP tools

## Core Concepts

MCP follows a simple model: the server exposes **tools**, the client (LLM) discovers and calls them. Each tool has a name, description, input schema, and an async handler function.

## Critical Patterns

### 1. Server Creation

Create the MCP server with a name that identifies the service.

```python
from mcp.server import Server

server = Server("my-server-name")
```

### 2. Tool Registration with Pydantic Schemas

Use `@server.tool()` decorator with Pydantic models for automatic JSON Schema generation. The function name becomes the tool name.

```python
from pydantic import BaseModel, Field
from mcp.server import Server

server = Server("factus-server")

class InvoiceParams(BaseModel):
    reference_code: str = Field(description="Unique reference code for the invoice")
    customer_identification: str = Field(description="Customer identification number")
    total: float = Field(gt=0, description="Invoice total amount")

@server.tool()
async def create_invoice(params: InvoiceParams) -> dict:
    """Create a new electronic invoice in Factus."""
    # Implementation...
    return {"status": "success", "reference": params.reference_code}
```

### 3. Tool Registration with Explicit Schema

Alternative: define the schema as a dict for dynamic or simpler tools.

```python
@server.tool()
async def get_customer(identification: str) -> dict:
    """Look up a customer by identification number."""
    # Implementation...
    return {"found": True, "customer": customer_data}
```

### 4. Tool Discovery

MCP automatically exposes tools via the `list_tools` request. The function docstring becomes the tool description. The type hints become the JSON Schema.

```python
@server.tool()
async def search_products(query: str, category: str | None = None) -> list[dict]:
    """Search products by query text, optionally filtered by category.

    Args:
        query: Free text search query
        category: Optional product category filter
    """
    ...
```

### 5. Error Handling in Tools

Return structured error responses instead of raising exceptions. Use try/except inside tool handlers.

```python
@server.tool()
async def process_payment(invoice_id: int, amount: float) -> dict:
    """Process payment for an invoice."""
    try:
        # Business logic...
        return {"success": True, "transaction_id": "txn-123"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Internal error: {e}"}
```

### 6. Server Lifecycle

Use the lifespan pattern for startup/shutdown logic (e.g., creating DB connections, validating config).

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[None]:
    """Initialize and cleanup server resources."""
    # Startup
    settings = validate_config()
    await create_db_and_tables(settings)
    print("Server initialized")

    yield

    # Shutdown
    print("Server shutting down")

server = Server("factus-server", lifespan=server_lifespan)
```

### 7. Running the Server

Two transport modes:
- **stdio**: Default, for LLM-hosted subprocess communication
- **sse**: For HTTP-based remote access

```python
import asyncio
from mcp.server.stdio import stdio_server

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

asyncio.run(main())
```

### 8. Dependency Injection Pattern

Inject external dependencies (API clients, DB sessions) via closures or class methods.

```python
class FactusServer:
    def __init__(self, api_client: FactusClient, db_session_factory):
        self.server = Server("factus-server")
        self.api = api_client
        self.db = db_session_factory
        self._register_tools()

    def _register_tools(self):
        @self.server.tool()
        async def list_customers() -> list[dict]:
            async with self.db() as session:
                repo = CustomerRepository(session)
                customers = await repo.list_all()
                return [c.model_dump() for c in customers]

    async def run_stdio(self):
        async with stdio_server() as (read, write):
            await self.server.run(read, write, self.server.create_initialization_options())
```

## Commands

```bash
# Install the MCP Python library
pip install "mcp[cli]"

# Run the server in stdio mode (default)
python server.py

# Test tool invocation via CLI
mcp run server.py

# Run with SSE transport (for remote access)
mcp run server.py --transport sse --port 8080
```

## Resources

- **MCP Specification**: https://spec.modelcontextprotocol.io
- **Python SDK**: https://github.com/modelcontextprotocol/python-sdk

## Critical Warnings

- Use `@server.tool()` NOT `@server.list_tools()` — the latter is for custom discovery, rarely needed
- Function docstrings become tool descriptions — write them for the LLM, not for humans
- Type hints become JSON Schema — use `str | None` for optional params, not `Optional[str]`
- Always wrap tool body in try/except — never let exceptions bubble up to MCP transport
- `Server("name")` constructor does NOT start anything — you must call `server.run()` explicitly
- The stdio transport reads from stdin and writes to stdout — never print() in a stdio server (use logging instead)
