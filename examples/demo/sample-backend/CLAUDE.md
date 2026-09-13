# Milestone API — working rules

- Stack: Python 3.11+, FastAPI, SQLite via `sqlite3` (no ORM), Pydantic v2, `uv` for dependencies.
- Run: `uv run uvicorn app.main:app --reload --port 8010`. Tests: `uv run pytest` (they use a throwaway database).
- Layout: `app/main.py` routes, `app/schemas.py` request/response models, `app/db.py` schema + seed + connections, `app/auth.py` JWT and passwords.
- Every route change ships with a test in `tests/test_api.py`. Validation belongs in the schemas, not in the handlers.
- Errors: `HTTPException` with a short lowercase message the frontend can display; 404 for a missing resource, 422 for invalid input.
- Schema changes go in `SCHEMA` (additive, `CREATE TABLE IF NOT EXISTS`); existing databases are not migrated, document when a `data.db` must be deleted.
- Keep the API contract in sync with the frontend client (`sample-frontend/src/lib/api.ts`).
