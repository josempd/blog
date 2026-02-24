import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, SQLModel


class PostUpsert(SQLModel):
    title: str = Field(max_length=255)
    slug: str = Field(max_length=255)
    excerpt: str | None = Field(default=None, max_length=500)
    content_markdown: str
    content_html: str
    published: bool = False
    published_at: datetime | None = None


class TagCreate(SQLModel):
    name: str = Field(max_length=100)
    slug: str = Field(max_length=100)


class TagPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class TagWithCount(TagPublic):
    post_count: int


class PostPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    excerpt: str | None = None
    published: bool
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tags: list[TagPublic] = []


class PostDetail(PostPublic):
    content_html: str


class PostsPublic(BaseModel):
    data: list[PostPublic]
    count: int
