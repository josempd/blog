from unittest.mock import patch

import pytest
from sqlmodel import Session

from app import crud
from app.core.exceptions import BadRequestError
from app.models import User
from app.schemas import UserCreate
from app.services import auth as auth_service
from app.utils import generate_password_reset_token
from tests.utils.utils import random_email, random_lower_string


def test_login_success(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    crud.create_user(session=db, user_create=user_in)

    user = auth_service.login(session=db, email=email, password=password)

    assert isinstance(user, User)
    assert user.email == email


def test_login_incorrect_password(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    crud.create_user(session=db, user_create=user_in)

    with pytest.raises(BadRequestError) as exc_info:
        auth_service.login(session=db, email=email, password=random_lower_string())

    assert "Incorrect email or password" in str(exc_info.value)


def test_login_inactive_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    crud.create_user(session=db, user_create=user_in)

    with pytest.raises(BadRequestError) as exc_info:
        auth_service.login(session=db, email=email, password=password)

    assert "Inactive user" in str(exc_info.value)


def test_recover_password_existing_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    crud.create_user(session=db, user_create=user_in)

    with (
        patch("app.services.auth.send_email", return_value=None),
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        result = auth_service.recover_password(session=db, email=email)

    assert result == "If that email is registered, we sent a password recovery link"


def test_recover_password_nonexistent_email(db: Session) -> None:
    email = random_email()

    result = auth_service.recover_password(session=db, email=email)

    assert result == "If that email is registered, we sent a password recovery link"


def test_reset_password_valid(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    crud.create_user(session=db, user_create=user_in)

    new_password = random_lower_string()
    token = generate_password_reset_token(email=email)

    auth_service.reset_password(session=db, token=token, new_password=new_password)

    authenticated = crud.authenticate(session=db, email=email, password=new_password)
    assert authenticated is not None
    assert authenticated.email == email


def test_reset_password_invalid_token(db: Session) -> None:
    with pytest.raises(BadRequestError) as exc_info:
        auth_service.reset_password(
            session=db, token="not.a.valid.token", new_password=random_lower_string()
        )

    assert "Invalid token" in str(exc_info.value)


def test_reset_password_inactive_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    crud.create_user(session=db, user_create=user_in)

    token = generate_password_reset_token(email=email)

    with pytest.raises(BadRequestError) as exc_info:
        auth_service.reset_password(
            session=db, token=token, new_password=random_lower_string()
        )

    assert "Inactive user" in str(exc_info.value)
