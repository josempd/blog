from sqlmodel import SQLModel


class HealthCheckResponse(SQLModel):
    status: str


class Message(SQLModel):
    message: str
