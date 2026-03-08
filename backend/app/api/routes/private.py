from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.models import User
from app.schemas import UserCreate, UserPublic
from app.services import user as user_service

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> User:
    """
    Create a new user.
    """
    user_create = UserCreate(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
    )
    return user_service.create_user(session=session, user_in=user_create)
