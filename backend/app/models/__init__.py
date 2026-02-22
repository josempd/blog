from sqlmodel import SQLModel  # noqa: F401 — needed by alembic/env.py

from app.models.post import Post, PostTagLink, Tag  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.user import User, UserBase  # noqa: F401
