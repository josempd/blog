import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, SQLModel


class ProjectUpsert(SQLModel):
    title: str = Field(max_length=255)
    slug: str = Field(max_length=255)
    description: str | None = None
    content_markdown: str | None = None
    content_html: str | None = None
    url: str | None = Field(default=None, max_length=500)
    repo_url: str | None = Field(default=None, max_length=500)
    featured: bool = False
    sort_order: int = 0


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    github_stars: int | None = None
    github_language: str | None = None
    github_forks: int | None = None
    github_last_pushed_at: datetime | None = None


class ProjectDetail(ProjectPublic):
    content_html: str | None = None


class ProjectsPublic(BaseModel):
    data: list[ProjectPublic]
    count: int
