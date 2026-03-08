from slowapi import Limiter
from starlette.requests import Request

LOGIN_RATE_LIMIT = "5/minute"
PASSWORD_RECOVERY_RATE_LIMIT = "3/minute"
RESET_PASSWORD_RATE_LIMIT = "3/minute"


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=get_client_ip)
