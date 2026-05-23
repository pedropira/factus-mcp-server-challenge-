# MCP Server Specification

## Purpose

Orchestration layer that initializes the MCP server, wires dependencies, registers all tools/resources/prompts, and runs stdio transport.

## Requirements

### Requirement: Server Initialization

The server MUST initialize with name `"factus-server"` and a lifespan that creates all dependencies.

#### Scenario: Server starts cleanly

- GIVEN a valid `.env` with Factus credentials
- WHEN the server starts
- THEN `create_db_and_tables()` runs (idempotent)
- THEN a `FactusClient` and all service instances are created
- THEN stdio transport begins accepting requests

### Requirement: Dependency Injection

The lifespan MUST produce a `ServerDeps` dataclass containing all shared dependencies.

#### Scenario: Services are singletons per server lifetime

- GIVEN the server is running
- WHEN two tools call the same service
- THEN both share the same `FactusClient` instance

#### Scenario: DB sessions are per-request

- GIVEN a tool requiring DB access
- WHEN the tool handler runs
- THEN a new `AsyncSession` is created and closed on completion

### Requirement: Tool Discovery

All registered tools MUST be discoverable via MCP `list_tools` request.

#### Scenario: All tools appear in listing

- GIVEN the server is running
- WHEN a client sends `list_tools`
- THEN the response contains all ~50 tool names with descriptions and JSON Schemas

### Requirement: Error Containment

Tool errors MUST NOT propagate to the MCP transport layer.

#### Scenario: Service error returns structured response

- GIVEN a tool that calls a service
- WHEN the service raises an exception
- THEN the tool catches it and returns `{"success": false, "error": str(e)}`
- THEN the server continues running
