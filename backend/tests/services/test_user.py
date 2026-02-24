import uuid

import pytest
from sqlmodel import Session

from app import crud
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.schemas import UserCreate, UserRegister, UserUpdate, UserUpdateMe
from app.services import user as user_service
from tests.utils.utils import random_email, random_lower_string


def test_create_user_email_conflict(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    crud.create_user(session=db, user_create=user_in)

    with pytest.raises(
        ConflictError, match="The user with this email already exists in the system."
    ):
        user_service.create_user(
            session=db, user_in=UserCreate(email=email, password=random_lower_string())
        )


def test_register_user_success(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserRegister(email=email, password=password)

    user = user_service.register_user(session=db, user_in=user_in)

    assert user.email == email


def test_register_user_email_conflict(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    crud.create_user(session=db, user_create=user_in)

    with pytest.raises(
        ConflictError, match="The user with this email already exists in the system$"
    ):
        user_service.register_user(
            session=db,
            user_in=UserRegister(email=email, password=random_lower_string()),
        )


def test_update_user_me_email_conflict(db: Session) -> None:
    email1 = random_email()
    email2 = random_email()
    password = random_lower_string()
    user1 = crud.create_user(
        session=db, user_create=UserCreate(email=email1, password=password)
    )
    user2 = crud.create_user(
        session=db, user_create=UserCreate(email=email2, password=password)
    )

    with pytest.raises(ConflictError, match="User with this email already exists"):
        user_service.update_user_me(
            session=db,
            user_in=UserUpdateMe(email=user1.email),
            current_user=user2,
        )


def test_update_user_me_own_email_ok(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )

    updated = user_service.update_user_me(
        session=db,
        user_in=UserUpdateMe(email=email),
        current_user=user,
    )

    assert updated.email == email


def test_update_password_me_wrong_password(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )

    with pytest.raises(BadRequestError, match="Incorrect password"):
        user_service.update_password_me(
            session=db,
            current_password=random_lower_string(),
            new_password=random_lower_string(),
            current_user=user,
        )


def test_update_password_me_same_password(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )

    with pytest.raises(
        BadRequestError, match="New password cannot be the same as the current one"
    ):
        user_service.update_password_me(
            session=db,
            current_password=password,
            new_password=password,
            current_user=user,
        )


def test_delete_user_me_superuser_prevented(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    superuser = crud.create_user(
        session=db,
        user_create=UserCreate(email=email, password=password, is_superuser=True),
    )

    with pytest.raises(
        ForbiddenError, match="Super users are not allowed to delete themselves"
    ):
        user_service.delete_user_me(session=db, current_user=superuser)


def test_delete_user_me_success(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )

    user_service.delete_user_me(session=db, current_user=user)

    assert crud.get_user_by_email(session=db, email=email) is None


def test_get_user_by_id_self(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )

    result = user_service.get_user_by_id(
        session=db, user_id=user.id, requesting_user=user
    )

    assert result.id == user.id


def test_get_user_by_id_other_as_normal_user(db: Session) -> None:
    password = random_lower_string()
    user1 = crud.create_user(
        session=db, user_create=UserCreate(email=random_email(), password=password)
    )
    user2 = crud.create_user(
        session=db, user_create=UserCreate(email=random_email(), password=password)
    )

    with pytest.raises(ForbiddenError, match="The user doesn't have enough privileges"):
        user_service.get_user_by_id(session=db, user_id=user1.id, requesting_user=user2)


def test_get_user_by_id_not_found(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    superuser = crud.create_user(
        session=db,
        user_create=UserCreate(email=email, password=password, is_superuser=True),
    )
    nonexistent_id = uuid.uuid4()

    with pytest.raises(NotFoundError, match="User not found"):
        user_service.get_user_by_id(
            session=db, user_id=nonexistent_id, requesting_user=superuser
        )


def test_update_user_not_found(db: Session) -> None:
    nonexistent_id = uuid.uuid4()

    with pytest.raises(NotFoundError, match="User not found"):
        user_service.update_user(
            session=db,
            user_id=nonexistent_id,
            user_in=UserUpdate(full_name=random_lower_string()),
        )


def test_delete_user_self_prevented(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    superuser = crud.create_user(
        session=db,
        user_create=UserCreate(email=email, password=password, is_superuser=True),
    )

    with pytest.raises(
        ForbiddenError, match="Super users are not allowed to delete themselves"
    ):
        user_service.delete_user(
            session=db, user_id=superuser.id, requesting_user=superuser
        )
