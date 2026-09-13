# Milestone API

The backend of the Milestone demo: projects and tasks behind a JWT login. FastAPI, SQLite through the standard library, Pydantic models. No ORM, no migrations: the schema is created at startup and an empty database gets demo data.

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8010    # docs at http://localhost:8010/docs
uv run pytest
```

Demo account: `admin@example.com` / `admin`.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Liveness, no auth. |
| `POST /api/auth/login`, `GET /api/auth/me` | Token issue and current user. |
| `GET /api/stats` | Project and task counts, tasks by status. |
| `GET/POST /api/projects`, `GET/DELETE /api/projects/{id}` | Projects with `task_count` and `done_count`. |
| `GET/POST /api/projects/{id}/tasks?status=` | Tasks of a project, ordered by priority. |
| `PATCH/DELETE /api/tasks/{id}` | Title, status (`todo`, `doing`, `done`) and priority (1 to 3). |

Every route except health and login needs `Authorization: Bearer <token>`.

The database file is `data.db` next to this directory, or the path in `SAMPLE_DB`. Delete it to get the demo data back.
