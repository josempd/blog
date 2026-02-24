import uuid
from datetime import datetime

from sqlmodel import SQLModel


class PostUpsert(SQLModel):
    title: str
    slug: str
    excerpt: str | None = None
    content_markdown: str
    content_html: str
    published: bool = False
    published_at: datetime | None = None


class TagPublic(SQLModel):
    id: uuid.UUID
    name: str
    slug: str


class TagWithCount(TagPublic):
    post_count: int


class PostPublic(SQLModel):
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


class PostsPublic(SQLModel):
    data: list[PostPublic]
    count: int
