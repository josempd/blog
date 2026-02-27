from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.deps import SessionDep
from app.pages.deps import is_htmx_request, templates
from app.services import blog as blog_service

router = APIRouter()


@router.get("/")
async def home(request: Request, session: SessionDep):
    posts, count = blog_service.list_published_posts(session=session, limit=5)
    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {
            "posts": posts,
            "has_more": count > 5,
        },
    )


@router.get("/blog")
async def blog_list(
    request: Request,
    session: SessionDep,
    tag: str | None = None,
    skip: int = 0,
):
    limit = 10
    posts, count = blog_service.list_published_posts(
        session=session,
        tag_slug=tag,
        skip=skip,
        limit=limit,
    )
    has_more = (skip + limit) < count
    next_url = f"/blog?skip={skip + limit}"
    if tag:
        next_url += f"&tag={tag}"

    context = {
        "posts": posts,
        "has_more": has_more,
        "next_url": next_url,
        "active_tag": tag,
    }

    if is_htmx_request(request):
        return templates.TemplateResponse(
            request, "pages/blog_list_partial.html", context
        )

    tags = blog_service.list_tags(session=session)
    context["tags"] = tags
    return templates.TemplateResponse(request, "pages/blog_list.html", context)


@router.get("/search")
async def search(request: Request, session: SessionDep, q: str = ""):
    results = blog_service.search_published_posts(session=session, query=q, limit=20)
    context = {"request": request, "posts": results, "query": q}
    if is_htmx_request(request):
        return templates.TemplateResponse(
            request, "pages/search_results_partial.html", context
        )
    return templates.TemplateResponse(request, "pages/search.html", context)


@router.get("/blog/{slug}.md")
async def blog_detail_md(slug: str, session: SessionDep):
    post = blog_service.get_published_post(session=session, slug=slug)
    return Response(
        content=post.content_markdown, media_type="text/markdown; charset=utf-8"
    )


@router.get("/blog/{slug}")
async def blog_detail(request: Request, session: SessionDep, slug: str):
    post, toc = blog_service.get_published_post_with_toc(session=session, slug=slug)
    return templates.TemplateResponse(
        request,
        "pages/blog_post.html",
        {"post": post, "toc": toc},
    )
