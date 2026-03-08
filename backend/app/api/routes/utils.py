from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.core.exceptions import ServiceUnavailableError
from app.schemas import HealthCheckResponse, Message
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
def health_check(session: SessionDep) -> HealthCheckResponse:
    try:
        session.exec(select(1))
    except SQLAlchemyError as exc:
        raise ServiceUnavailableError("Database is not reachable") from exc
    return HealthCheckResponse(status="healthy")
