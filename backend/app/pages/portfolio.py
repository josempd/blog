from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.deps import SessionDep
from app.pages.deps import content_dir, templates
from app.services import portfolio as portfolio_service

router = APIRouter()


@router.get("/projects")
async def projects(request: Request, session: SessionDep):
    project_list, count = portfolio_service.list_projects(session=session, limit=50)
    return templates.TemplateResponse(
        request,
        "pages/projects.html",
        {"projects": project_list},
    )


@router.get("/about")
async def about(request: Request):
    page = portfolio_service.get_about_page(content_dir=content_dir())
    return templates.TemplateResponse(
        request,
        "pages/about.html",
        {"page": page},
    )
