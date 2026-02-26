from __future__ import annotations

from fastapi import APIRouter, Request

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


@router.get("/blog/{slug}")
async def blog_detail(request: Request, session: SessionDep, slug: str):
    post = blog_service.get_published_post(session=session, slug=slug)
    return templates.TemplateResponse(
        request,
        "pages/blog_post.html",
        {"post": post},
    )
