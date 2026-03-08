from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette.requests import Request

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.rate_limit import (
    LOGIN_RATE_LIMIT,
    PASSWORD_RECOVERY_RATE_LIMIT,
    RESET_PASSWORD_RATE_LIMIT,
    limiter,
)
from app.models import User
from app.schemas import Message, NewPassword, Token, UserPublic
from app.services import auth as auth_service

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
@limiter.limit(LOGIN_RATE_LIMIT)
def login_access_token(
    request: Request,  # noqa: ARG001 — required by SlowAPI
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = auth_service.login(
        session=session, email=form_data.username, password=form_data.password
    )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            str(user.id), expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> User:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
@limiter.limit(PASSWORD_RECOVERY_RATE_LIMIT)
def recover_password(request: Request, email: str, session: SessionDep) -> Message:  # noqa: ARG001
    """
    Password Recovery
    """
    message = auth_service.recover_password(session=session, email=email)
    return Message(message=message)


@router.post("/reset-password/")
@limiter.limit(RESET_PASSWORD_RATE_LIMIT)
def reset_password(request: Request, session: SessionDep, body: NewPassword) -> Message:  # noqa: ARG001
    """
    Reset password
    """
    auth_service.reset_password(
        session=session, token=body.token, new_password=body.new_password
    )
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> HTMLResponse:
    """
    HTML Content for Password Recovery
    """
    html_content, subject = auth_service.get_password_recovery_html(
        session=session, email=email
    )
    return HTMLResponse(content=html_content, headers={"subject:": subject})
