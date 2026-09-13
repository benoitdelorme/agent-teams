"""Milestone API: projects and tasks behind a JWT login. FastAPI + SQLite, no ORM.

Run: uv run uvicorn app.main:app --reload --port 8010   (docs at /docs)
"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .auth import create_token, get_current_user, verify_password
from .db import get_conn, init_db
from .schemas import LoginIn, Project, ProjectIn, Stats, Task, TaskIn, TaskPatch, TokenOut, User


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Milestone API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_dep = Depends(get_current_user)

PROJECT_SQL = """
SELECT p.*,
       (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) AS task_count,
       (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id AND t.status = 'done') AS done_count
FROM projects p
"""


def _project_or_404(c, project_id: int) -> Project:
    row = c.execute(PROJECT_SQL + " WHERE p.id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(404, "project not found")
    return Project(**dict(row))


# ---- health and auth --------------------------------------------------------
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenOut)
def login(body: LoginIn) -> TokenOut:
    with get_conn() as c:
        row = c.execute("SELECT id, email, name, created_at, password_hash FROM users WHERE email = ?", (body.email,)).fetchone()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "invalid credentials")
    user = User(id=row["id"], email=row["email"], name=row["name"], created_at=row["created_at"])
    return TokenOut(access_token=create_token(row["id"]), user=user)


@app.get("/api/auth/me", response_model=User)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


# ---- overview ---------------------------------------------------------------
@app.get("/api/stats", response_model=Stats, dependencies=[auth_dep])
def stats() -> Stats:
    with get_conn() as c:
        projects = c.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        tasks = c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        rows = c.execute("SELECT status, COUNT(*) AS n FROM tasks GROUP BY status").fetchall()
    by_status = {s: 0 for s in ("todo", "doing", "done")}
    by_status.update({r["status"]: r["n"] for r in rows})
    return Stats(projects=projects, tasks=tasks, by_status=by_status)


# ---- projects ---------------------------------------------------------------
@app.get("/api/projects", response_model=list[Project], dependencies=[auth_dep])
def list_projects() -> list[Project]:
    with get_conn() as c:
        rows = c.execute(PROJECT_SQL + " ORDER BY p.id").fetchall()
    return [Project(**dict(r)) for r in rows]


@app.post("/api/projects", response_model=Project, status_code=201, dependencies=[auth_dep])
def create_project(body: ProjectIn) -> Project:
    with get_conn() as c:
        cur = c.execute("INSERT INTO projects(name, description) VALUES (?,?)", (body.name, body.description))
        return _project_or_404(c, cur.lastrowid)


@app.get("/api/projects/{project_id}", response_model=Project, dependencies=[auth_dep])
def get_project(project_id: int) -> Project:
    with get_conn() as c:
        return _project_or_404(c, project_id)


@app.delete("/api/projects/{project_id}", status_code=204, dependencies=[auth_dep])
def delete_project(project_id: int) -> None:
    with get_conn() as c:
        if c.execute("DELETE FROM projects WHERE id = ?", (project_id,)).rowcount == 0:
            raise HTTPException(404, "project not found")


# ---- tasks ------------------------------------------------------------------
@app.get("/api/projects/{project_id}/tasks", response_model=list[Task], dependencies=[auth_dep])
def list_tasks(project_id: int, status: str | None = None) -> list[Task]:
    with get_conn() as c:
        _project_or_404(c, project_id)
        query, args = "SELECT * FROM tasks WHERE project_id = ?", [project_id]
        if status:
            query += " AND status = ?"
            args.append(status)
        rows = c.execute(query + " ORDER BY priority, id", args).fetchall()
    return [Task(**dict(r)) for r in rows]


@app.post("/api/projects/{project_id}/tasks", response_model=Task, status_code=201, dependencies=[auth_dep])
def create_task(project_id: int, body: TaskIn) -> Task:
    with get_conn() as c:
        _project_or_404(c, project_id)
        cur = c.execute("INSERT INTO tasks(project_id, title, status, priority) VALUES (?,?,?,?)",
                        (project_id, body.title, body.status, body.priority))
        row = c.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return Task(**dict(row))


@app.patch("/api/tasks/{task_id}", response_model=Task, dependencies=[auth_dep])
def patch_task(task_id: int, body: TaskPatch) -> Task:
    fields = body.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(400, "nothing to update")
    assignments = ", ".join(f"{k} = ?" for k in fields)          # keys are validated by the schema
    with get_conn() as c:
        if c.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", [*fields.values(), task_id]).rowcount == 0:
            raise HTTPException(404, "task not found")
        row = c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return Task(**dict(row))


@app.delete("/api/tasks/{task_id}", status_code=204, dependencies=[auth_dep])
def delete_task(task_id: int) -> None:
    with get_conn() as c:
        if c.execute("DELETE FROM tasks WHERE id = ?", (task_id,)).rowcount == 0:
            raise HTTPException(404, "task not found")
