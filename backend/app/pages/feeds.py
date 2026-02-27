from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.deps import SessionDep
from app.pages.deps import templates
from app.services import blog as blog_service
from app.services import portfolio as portfolio_service

router = APIRouter()


@router.get("/feed.xml")
async def rss_feed(request: Request, session: SessionDep):
    posts, _ = blog_service.list_published_posts(session=session, limit=50)
    base_url = str(request.base_url)
    return templates.TemplateResponse(
        request,
        "feeds/rss.xml",
        {"posts": posts, "base_url": base_url},
        media_type="application/rss+xml",
    )


@router.get("/sitemap.xml")
async def sitemap(request: Request, session: SessionDep):
    posts, _ = blog_service.list_published_posts(session=session, limit=1000)
    projects, _ = portfolio_service.list_projects(session=session, limit=1000)
    base_url = str(request.base_url)
    return templates.TemplateResponse(
        request,
        "feeds/sitemap.xml",
        {"posts": posts, "projects": projects, "base_url": base_url},
        media_type="application/xml",
    )


@router.get("/llms.txt")
async def llms_txt(request: Request, session: SessionDep):
    posts, _ = blog_service.list_published_posts(session=session, limit=1000)
    projects, _ = portfolio_service.list_projects(session=session, limit=1000)
    base_url = str(request.base_url)
    return templates.TemplateResponse(
        request,
        "feeds/llms.txt",
        {"posts": posts, "projects": projects, "base_url": base_url},
        media_type="text/plain",
    )


@router.get("/llms-full.txt")
async def llms_full_txt(request: Request, session: SessionDep):
    posts, _ = blog_service.list_published_posts(session=session, limit=1000)
    base_url = str(request.base_url)
    return templates.TemplateResponse(
        request,
        "feeds/llms_full.txt",
        {"posts": posts, "base_url": base_url},
        media_type="text/plain",
    )


@router.get("/robots.txt")
async def robots_txt(request: Request):
    base_url = str(request.base_url)
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "# AI crawlers — explicitly welcome\n"
        "User-agent: GPTBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: ClaudeBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: Google-Extended\n"
        "Allow: /\n"
        "\n"
        "User-agent: PerplexityBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: CCBot\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {base_url}sitemap.xml\n"
    )
    return Response(content=body, media_type="text/plain")
