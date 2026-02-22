import uuid
from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlmodel import Field, SQLModel

from app.models.base import get_datetime_utc


class Project(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    slug: str = Field(max_length=255, unique=True, index=True)
    description: str | None = Field(default=None, sa_type=Text)
    content_markdown: str | None = Field(default=None, sa_type=Text)
    content_html: str | None = Field(default=None, sa_type=Text)
    url: str | None = Field(default=None, max_length=500)
    repo_url: str | None = Field(default=None, max_length=500)
    featured: bool = Field(default=False)
    sort_order: int = Field(default=0)
    source_path: str | None = Field(default=None, max_length=500, unique=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
