"""API tests on a throwaway database (SAMPLE_DB is read when app.db is imported)."""
import os
import tempfile

os.environ["SAMPLE_DB"] = tempfile.mktemp(suffix=".db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def auth_headers() -> dict:
    r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health_is_public():
    with client:
        assert client.get("/api/health").json() == {"status": "ok"}


def test_login_returns_a_token_and_the_user():
    with client:
        r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin"})
        assert r.status_code == 200
        body = r.json()
        assert body["access_token"] and body["token_type"] == "bearer"
        assert body["user"]["email"] == "admin@example.com"


def test_login_rejects_a_bad_password():
    with client:
        r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"})
        assert r.status_code == 401
        assert r.json() == {"detail": "invalid credentials"}


def test_protected_routes_need_a_token():
    with client:
        for path in ("/api/auth/me", "/api/projects", "/api/stats"):
            r = client.get(path)
            assert r.status_code == 401, path
            assert r.json() == {"detail": "not authenticated"}


def test_seed_data_is_present():
    with client:
        projects = client.get("/api/projects", headers=auth_headers()).json()
        assert [p["name"] for p in projects][:3] == ["Website redesign", "Mobile app", "Internal tools"]
        assert projects[0]["task_count"] == 5 and projects[0]["done_count"] == 2


def test_project_and_task_lifecycle():
    with client:
        headers = auth_headers()
        p = client.post("/api/projects", json={"name": "Launch", "description": "Q4 launch"}, headers=headers)
        assert p.status_code == 201
        project = p.json()
        assert project["task_count"] == 0

        t = client.post(f"/api/projects/{project['id']}/tasks", json={"title": "Write the announcement", "priority": 1}, headers=headers)
        assert t.status_code == 201
        task = t.json()
        assert task["status"] == "todo"

        assert client.patch(f"/api/tasks/{task['id']}", json={"status": "done"}, headers=headers).json()["status"] == "done"
        assert client.get(f"/api/projects/{project['id']}", headers=headers).json()["done_count"] == 1
        assert client.get(f"/api/projects/{project['id']}/tasks?status=done", headers=headers).json()[0]["id"] == task["id"]
        assert client.get(f"/api/projects/{project['id']}/tasks?status=todo", headers=headers).json() == []

        assert client.get("/api/stats", headers=headers).json()["projects"] == 4
        assert client.delete(f"/api/projects/{project['id']}", headers=headers).status_code == 204
        assert client.get(f"/api/projects/{project['id']}", headers=headers).status_code == 404
        assert client.get(f"/api/tasks/{task['id']}", headers=headers).status_code in (404, 405)


def test_validation_and_missing_resources():
    with client:
        headers = auth_headers()
        assert client.post("/api/projects", json={"name": ""}, headers=headers).status_code == 422
        assert client.post("/api/projects/999/tasks", json={"title": "x"}, headers=headers).status_code == 404
        assert client.patch("/api/tasks/999", json={"status": "done"}, headers=headers).status_code == 404
        assert client.patch("/api/tasks/1", json={}, headers=headers).status_code == 400
        assert client.patch("/api/tasks/1", json={"status": "later"}, headers=headers).status_code == 422
