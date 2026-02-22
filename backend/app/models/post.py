import uuid
from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc


class PostTagLink(SQLModel, table=True):
    post_id: uuid.UUID = Field(
        foreign_key="post.id", primary_key=True, ondelete="CASCADE"
    )
    tag_id: uuid.UUID = Field(
        foreign_key="tag.id", primary_key=True, ondelete="CASCADE"
    )


class Tag(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    slug: str = Field(max_length=100, unique=True, index=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    posts: list["Post"] = Relationship(back_populates="tags", link_model=PostTagLink)


class Post(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    slug: str = Field(max_length=255, unique=True, index=True)
    excerpt: str | None = Field(default=None, max_length=500)
    content_markdown: str = Field(sa_type=Text)
    content_html: str = Field(sa_type=Text)
    published: bool = Field(default=False)
    published_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    source_path: str | None = Field(default=None, max_length=500, unique=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    tags: list[Tag] = Relationship(back_populates="posts", link_model=PostTagLink)
