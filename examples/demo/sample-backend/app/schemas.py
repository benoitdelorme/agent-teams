"""Request and response models. Validation lives here, not in the handlers."""
from typing import Literal
from pydantic import BaseModel, Field

Status = Literal["todo", "doing", "done"]


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""


class Project(ProjectIn):
    id: int
    created_at: str
    task_count: int = 0
    done_count: int = 0


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    status: Status = "todo"
    priority: int = Field(default=2, ge=1, le=3)


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: Status | None = None
    priority: int | None = Field(default=None, ge=1, le=3)


class Task(TaskIn):
    id: int
    project_id: int
    created_at: str


class Stats(BaseModel):
    projects: int
    tasks: int
    by_status: dict[str, int]


class User(BaseModel):
    id: int
    email: str
    name: str
    created_at: str


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
