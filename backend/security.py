from __future__ import annotations

from collections import defaultdict, deque
from time import time

from fastapi import Request

from backend.config import get_settings
from backend.services.metrics_service import runtime_metrics


WINDOW_SECONDS = 60
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
AUTH_EXEMPT_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}
_requests_by_key: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_key(request: Request) -> str:
    return f"{client_ip(request)}:{request.method}:{request.url.path}"


def check_rate_limit(request: Request) -> tuple[bool, int]:
    settings = get_settings()
    if request.url.path == "/live/tick":
        limit = max(settings.rate_limit_write_per_minute, 30)
    else:
        limit = (
            settings.rate_limit_write_per_minute
            if request.method.upper() in WRITE_METHODS
            else settings.rate_limit_per_minute
        )
    now = time()
    bucket = _requests_by_key[rate_limit_key(request)]

    while bucket and now - bucket[0] > WINDOW_SECONDS:
        bucket.popleft()

    if len(bucket) >= limit:
        runtime_metrics.record_rate_limit_hit()
        return False, limit

    bucket.append(now)
    return True, limit


def request_too_large(request: Request) -> bool:
    content_length = request.headers.get("content-length")
    if not content_length:
        return False
    try:
        return int(content_length) > get_settings().max_request_bytes
    except ValueError:
        return True


def authenticated(request: Request) -> bool:
    settings = get_settings()
    if not settings.api_key:
        return True
    path = request.url.path
    if path in AUTH_EXEMPT_PATHS or path.startswith("/eda-assets/"):
        return True
    return request.headers.get("x-api-key") == settings.api_key


def security_headers() -> dict[str, str]:
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; object-src 'none'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }
