# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| When running android commands or managing sdk/devices | android-cli | C:\Users\pedro daniel\.gemini\config\plugins\android-cli-plugin\skills\SKILL.md |
| When creating a pull request, opening a PR, or preparing changes for review | branch-pr | C:\Users\pedro daniel\.gemini\config\skills\branch-pr\SKILL.md |
| When writing Go tests, using teatest, or adding test coverage | go-testing | C:\Users\pedro daniel\.gemini\config\skills\go-testing\SKILL.md |
| When creating a GitHub issue, reporting a bug, or requesting a feature | issue-creation | C:\Users\pedro daniel\.gemini\config\skills\issue-creation\SKILL.md |
| When user says "judgment day", "judgment-day", "review adversarial", "dual review", "doble review", "juzgar", "que lo juzguen" | judgment-day | C:\Users\pedro daniel\.gemini\config\skills\judgment-day\SKILL.md |
| When user asks to create a new skill, add agent instructions, or document patterns for AI | skill-creator | C:\Users\pedro daniel\.gemini\config\skills\skill-creator\SKILL.md |
| When working with SQLModel models, async sessions, JSON columns, or repositories | sqlmodel-async | C:\Users\pedro daniel\OneDrive\Desktop\factus_mcp_server\.agents\skills\sqlmodel-async\SKILL.md |
| When creating HTTP clients, implementing auth flows, or making async API requests | httpx-patterns | C:\Users\pedro daniel\OneDrive\Desktop\factus_mcp_server\.agents\skills\httpx-patterns\SKILL.md |
| When creating MCP servers, registering tools, or defining tool schemas | mcp-server-python | C:\Users\pedro daniel\OneDrive\Desktop\factus_mcp_server\.agents\skills\mcp-server-python\SKILL.md |
| When writing pytest tests, fixtures, mocks, or async test cases | python-testing-patterns | C:\Users\pedro daniel\OneDrive\Desktop\factus_mcp_server\.agents\skills\python-testing-patterns\SKILL.md |
| When defining Pydantic models, validators, serializers, or settings | pydantic | C:\Users\pedro daniel\OneDrive\Desktop\factus_mcp_server\.agents\skills\pydantic\SKILL.md |
| When writing FastAPI-style async code with dependency injection | fastapi-python | C:\Users\pedro daniel\OneDrive\Desktop\factus_mcp_server\.agents\skills\fastapi-python\SKILL.md |
| When setting up project structure, CRUD patterns, or service layers | fastapi-templates | C:\Users\pedro daniel\OneDrive\Desktop\factus_mcp_server\.agents\skills\fastapi-templates\SKILL.md |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### android-cli
- Use `android` or relevant android SDK CLI commands for tasks
- Ensure ANDROID_HOME environment variable is correctly set
- Match package/activity names precisely when running emulation or build
- Avoid using GUI commands, prefer CLI flags for headless automation

### branch-pr
- Every pull request MUST correspond to an existing issue. Check/create issue first.
- Branch name format: `issue-{id}-{kebab-case-description}`
- Commit message format: conventional commits only (e.g. `feat: add ...`, `fix: resolve ...`)
- Do NOT add AI attribution or "Co-Authored-By" tags to commits or PR descriptions

### go-testing
- Write tests matching standard Go test structure: `TestXxx(t *testing.T)`
- For Bubbletea TUI, use teatest framework to mock inputs and verify model state
- Ensure unit and integration tests run correctly via `go test ./...`
- Do not check in failing tests or commented-out assertions

### issue-creation
- Search GitHub for similar issues before creating a new one
- Title format: `[Component] Brief description`
- Body MUST include steps to reproduce, expected behavior, and actual behavior
- Label issues appropriately (e.g., `bug`, `feature`, `documentation`)

### judgment-day
- Trigger dual-blind judge sub-agents to review target codebase
- Keep judges independent and run them in parallel
- Synthesize judge findings into actionable items and apply fixes
- Re-run judgment up to 2 iterations before escalating if checks don't pass

### skill-creator
- Write skills to `skills/{skill-name}/SKILL.md`
- Include YAML frontmatter with `name`, `description`, `license`, and `metadata`
- Description must explicitly state the "Trigger:" condition
- Structure instructions into clear, actionable rules and patterns

### sqlmodel-async
- Use `sa_type=JSON` on `Field()` for nested API data; import `JSON` from `sqlalchemy`, not SQLModel
- Always import model modules BEFORE calling `create_all` — otherwise tables aren't registered in metadata
- `SQLModel.metadata.create_all` uses `conn.run_sync()` for async engines, never call directly
- Use `session.exec(select(...))` for queries, `session.get(Model, pk)` for PK lookup
- Do NOT use `sessionmaker` — instantiate `AsyncSession(engine)` directly
- Inject `AsyncSession` into repos via constructor; never pass engine to repos
- For get_or_create: check first, return `(existing, False)` or `(new, True)`
- Use `ilike` for case-insensitive search with `or_` for multi-field matching

### httpx-patterns
- httpx >= 0.28 uses `httpx.Auth` (NOT `AsyncAuth`) — `AsyncAuth` does NOT exist
- The `yield` in `async_auth_flow` cannot be extracted into a helper — must be inline
- Always use `asyncio.Lock()` (not `threading.Lock`) for async auth flow synchronization
- Always close client with `await client.aclose()` or use `async with`
- Set explicit `Timeout(30.0, connect=10.0, read=20.0)` to avoid hanging
- Retry 5xx/429 with exponential backoff (`2 ** attempt`); do not retry 4xx errors
- Pass dicts to `json=` param — httpx auto-serializes and sets Content-Type

### mcp-server-python
- Use `@server.tool()` to register tools — NOT `@server.list_tools()`
- Function docstrings become tool descriptions — write for the LLM, not humans
- Type hints become JSON Schema — use `str | None` not `Optional[str]` for optional params
- Always wrap tool body in try/except — never let exceptions bubble to MCP transport
- `Server("name")` constructor does NOT start anything — must call `server.run()` explicitly
- For stdio transport, never `print()` — use `logging` module instead
- Use lifespan pattern (`@asynccontextmanager`) for startup/shutdown logic

### python-testing-patterns
- Use AAA pattern (Arrange/Act/Assert) for all tests
- Use `@pytest.mark.asyncio` for async test functions with `anyio`
- Use `monkeypatch.setenv()` for env vars, `monkeypatch.setattr()` for object attributes
- Use `Mock()` with `return_value` / `side_effect` for external dependencies
- Use `@pytest.mark.parametrize` for multiple input combinations
- Use `tmp_path` fixture for temporary file operations
- Use `freezegun.freeze_time` for time-dependent scenarios

### pydantic
- Use `model_config = ConfigDict(...)` instead of `class Config`
- .dict() → .model_dump(), .json() → .model_dump_json()
- @validator → @field_validator with @classmethod
- @root_validator → @model_validator(mode='after')
- Use `Field(ge=0, le=150)` for constraints instead of custom validators
- Use `SecretStr` for sensitive data (won't print in logs/repr)
- Use `from_attributes=True` in ConfigDict for ORM mode

### fastapi-python
- Use `def` for pure functions, `async def` for async operations
- Use type hints with Pydantic models, not raw dicts
- Prefer lifespan context managers over startup/shutdown events
- Use HTTPException for expected errors, model as specific HTTP responses
- Handle edge cases at entry points with early returns (guard clauses)
- Use descriptive variable names with auxiliary verbs (`is_active`, `has_permission`)

### fastapi-templates
- Follow project structure: api/v1/endpoints, core, models, schemas, services, repositories
- Use FastAPI's `Depends()` for dependency injection (DB sessions, auth)
- CRUD repos: BaseRepository[T] with get, get_multi, create, update, delete
- Service layer acts as business logic between routes and repos
- Use `AsyncSession` with sessionmaker for DB sessions in dependencies

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | C:\Users\pedro daniel\OneDrive\Desktop\factus_mcp_server\AGENTS.md | Index — Development conventions, two-track workflow, skills |
