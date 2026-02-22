import uuid
from datetime import datetime

from sqlmodel import SQLModel


class ProjectPublic(SQLModel):
    id: uuid.UUID
    title: str
    slug: str
    description: str | None = None
    url: str | None = None
    repo_url: str | None = None
    featured: bool
    sort_order: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectsPublic(SQLModel):
    data: list[ProjectPublic]
    count: int
