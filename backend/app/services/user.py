import uuid

from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.core.security import verify_password
from app.models import User
from app.schemas import UserCreate, UserRegister, UserUpdate, UserUpdateMe
from app.utils import generate_new_account_email, send_email


def _check_email_available(
    *,
    session: Session,
    email: str,
    exclude_user_id: uuid.UUID | None = None,
    message: str = "User with this email already exists",
) -> None:
    existing = crud.get_user_by_email(session=session, email=email)
    if existing and (exclude_user_id is None or existing.id != exclude_user_id):
        raise ConflictError(message)


def create_user(*, session: Session, user_in: UserCreate) -> User:
    _check_email_available(
        session=session,
        email=user_in.email,
        message="The user with this email already exists in the system.",
    )
    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


def list_users(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[User], int]:
    return crud.get_users(session=session, skip=skip, limit=limit)


def register_user(*, session: Session, user_in: UserRegister) -> User:
    _check_email_available(
        session=session,
        email=user_in.email,
        message="The user with this email already exists in the system",
    )
    user_create = UserCreate.model_validate(user_in)
    return crud.create_user(session=session, user_create=user_create)


def get_user_by_id(
    *, session: Session, user_id: uuid.UUID, requesting_user: User
) -> User:
    user = crud.get_user_by_id(session=session, user_id=user_id)
    if user is not None and user == requesting_user:
        return user
    if not requesting_user.is_superuser:
        raise ForbiddenError("The user doesn't have enough privileges")
    if user is None:
        raise NotFoundError("User", user_id)
    return user


def update_user_me(
    *, session: Session, user_in: UserUpdateMe, current_user: User
) -> User:
    if user_in.email:
        _check_email_available(
            session=session,
            email=user_in.email,
            exclude_user_id=current_user.id,
        )
    return crud.update_user_me(session=session, user=current_user, user_in=user_in)


def update_password_me(
    *,
    session: Session,
    current_password: str,
    new_password: str,
    current_user: User,
) -> None:
    verified, _ = verify_password(current_password, current_user.hashed_password)
    if not verified:
        raise BadRequestError("Incorrect password")
    if current_password == new_password:
        raise BadRequestError("New password cannot be the same as the current one")
    crud.update_password(session=session, user=current_user, new_password=new_password)


def update_user(*, session: Session, user_id: uuid.UUID, user_in: UserUpdate) -> User:
    db_user = crud.get_user_by_id(session=session, user_id=user_id)
    if not db_user:
        raise NotFoundError("User", user_id)
    if user_in.email:
        _check_email_available(
            session=session,
            email=user_in.email,
            exclude_user_id=user_id,
        )
    return crud.update_user(session=session, db_user=db_user, user_in=user_in)


def delete_user_me(*, session: Session, current_user: User) -> None:
    if current_user.is_superuser:
        raise ForbiddenError("Super users are not allowed to delete themselves")
    crud.delete_user(session=session, user=current_user)


def delete_user(*, session: Session, user_id: uuid.UUID, requesting_user: User) -> None:
    user = crud.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise NotFoundError("User", user_id)
    if user == requesting_user:
        raise ForbiddenError("Super users are not allowed to delete themselves")
    crud.delete_user(session=session, user=user)
