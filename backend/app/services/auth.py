from sqlmodel import Session

from app import crud
from app.core.exceptions import BadRequestError, NotFoundError
from app.models import User
from app.schemas import UserUpdate
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)


def login(*, session: Session, email: str, password: str) -> User:
    user = crud.authenticate(session=session, email=email, password=password)
    if not user:
        raise BadRequestError("Incorrect email or password")
    if not user.is_active:
        raise BadRequestError("Inactive user")
    return user


def recover_password(*, session: Session, email: str) -> str:
    user = crud.get_user_by_email(session=session, email=email)
    if user:
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return "If that email is registered, we sent a password recovery link"


def reset_password(*, session: Session, token: str, new_password: str) -> None:
    email = verify_password_reset_token(token=token)
    if not email:
        raise BadRequestError("Invalid token")
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise BadRequestError("Invalid token")
    if not user.is_active:
        raise BadRequestError("Inactive user")
    crud.update_user(
        session=session,
        db_user=user,
        user_in=UserUpdate(password=new_password),
    )


def get_password_recovery_html(*, session: Session, email: str) -> tuple[str, str]:
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise NotFoundError("User", email)
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return email_data.html_content, email_data.subject
