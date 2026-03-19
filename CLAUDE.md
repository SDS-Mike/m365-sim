# CLAUDE.md - Project Rules for m365-sim

> Read at the start of every session to maintain consistency.

## Project Context

**m365-sim** is a Microsoft Graph API simulation platform. It is a **single-file FastAPI server** (`server.py`) that serves static JSON fixtures representing M365 tenant states. No database, no ORM, no package structure beyond the repo root.

**Consumer**: CMMC compliance assessment tools that deserialize responses into typed structs, so fixture JSON shapes must exactly match real Graph API responses.

## Project Structure

```
m365-sim/
├── server.py                          # Single-file FastAPI mock server
├── scenarios/
│   ├── gcc-moderate/
│   │   ├── greenfield/*.json          # Fresh G5 tenant, no controls
│   │   ├── hardened/*.json            # Post-remediation deploy
│   │   └── partial/                   # v2
│   └── gcc-high/
│       └── greenfield/*.json          # Placeholder fixtures (TODO)
├── builder/
│   └── tenant_builder.py             # Fluent API for programmatic fixtures
├── sdk/
│   └── __init__.py                   # Package entry point
├── tests/
│   ├── conftest.py                   # Subprocess server fixture
│   ├── test_server.py                # Greenfield endpoint tests
│   ├── test_query_write_error.py     # Query params, writes, error sim
│   ├── test_hardened.py              # Hardened scenario tests
│   └── test_tenant_builder.py        # Builder tests
├── docs/
│   └── decisions.md                  # Design decision log
├── requirements.txt                  # fastapi, uvicorn, pytest, httpx
├── PROJECT_BRIEF.md
├── DEVELOPMENT_PLAN.md
└── CLAUDE.md
```

## Tech Stack

- **Python 3.11+** — language
- **FastAPI** — web framework (use `lifespan` context manager, NOT `on_event`)
- **uvicorn** — ASGI server
- **pytest + httpx** — testing (subprocess server, real HTTP)
- **No database** — all data is static JSON fixtures
- **No Django, Flask, SQLAlchemy** — explicitly prohibited

## Key Conventions

### Server
- `server.py` is a **single file** — all routes, middleware, and startup logic live here
- Run with: `python server.py --scenario greenfield --cloud gcc-moderate --port 8888`
- Or: `uvicorn server:app --port 8888` (uses defaults)
- Auth: accept any `Bearer` token, return 401 if `Authorization` header missing entirely
- 404 handler: return JSON with the requested path, log warning for unmapped paths

### Fixtures
- All JSON must include `@odata.context` matching real Graph API responses
- GCC Moderate uses `graph.microsoft.com`, GCC High uses `graph.microsoft.us`
- Greenfield tenant identity: **Contoso Defense LLC**, domain `contoso-defense.com`
- Hardened CA policies MUST use `"state": "enabledForReportingButNotEnforced"` (never `"enabled"`)
- Break-glass account ID: `00000000-0000-0000-0000-000000000011`

### Graph API Patterns
- Use `(p.get("grantControls") or {}).get("builtInControls")` for nested access — `or {}` handles explicit null
- `$top=N` truncates `value` array; `$filter`/`$select`/`$expand` are logged but ignored

### Testing
- Tests use **subprocess server** — pytest fixture starts real server, tests hit real HTTP
- Test files use `mock_server` and `auth_headers` fixtures from `conftest.py`
- No mocking — all tests are integration tests against the actual server
- Coverage target: 80%

### Git
- One branch per **task** (not subtask): `feature/{phase}-{task}-{description}`
- One commit per subtask with semantic message: `feat(scope): description`
- Squash merge when task complete, delete branch, push to main

## Running

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start server
python server.py                                    # defaults
python server.py --scenario hardened --port 9999    # hardened on 9999

# Tests
pytest tests/ -v
pytest tests/test_server.py -v                      # greenfield only
pytest tests/test_hardened.py -v                     # hardened only
```

## Session Protocol

### Starting
1. Read DEVELOPMENT_PLAN.md — find the subtask
2. Verify prerequisites are marked `[x]`
3. Read prerequisite completion notes for context

### Ending
1. All subtask checkboxes checked `[x]`
2. All tests pass: `pytest tests/ -v`
3. No TODO/FIXME in non-scaffold code: `grep -r "TODO\|FIXME" server.py tests/`
4. Completion notes filled in DEVELOPMENT_PLAN.md
5. Git commit with semantic message

---

*Project: m365-sim | Updated: 2026-03-19*
