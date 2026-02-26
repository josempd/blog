from __future__ import annotations

from fastapi import APIRouter

from app.pages import blog, feeds, portfolio

pages_router = APIRouter(include_in_schema=False)
pages_router.include_router(blog.router)
pages_router.include_router(portfolio.router)
pages_router.include_router(feeds.router)
