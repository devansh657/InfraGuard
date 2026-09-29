from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import get_settings
from backend.api.routes_ai import router as ai_router
from backend.api.routes_anomaly import router as anomaly_router
from backend.api.routes_diagnose import router as diagnose_router
from backend.api.routes_history import router as history_router
from backend.api.routes_live import router as live_router
from backend.api.routes_model import router as model_router
from backend.api.routes_predict import router as predict_router
from backend.api.routes_report import router as report_router
from backend.api.routes_upload import router as upload_router
from backend.schemas.response_models import HealthResponse
from backend.security import authenticated, check_rate_limit, request_too_large, security_headers
from backend.services.db_service import check_database, initialize_database
from backend.services.metrics_service import runtime_metrics
from backend.services.ml_service import get_ml_service
from backend.utils.logger import configure_logging, get_logger


logger = get_logger(__name__)
settings = get_settings()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EDA_DIR = PROJECT_ROOT / "docs" / "eda"


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await run_in_threadpool(initialize_database)
    await run_in_threadpool(get_ml_service)
    logger.info("InfraGuard AI backend started")
    yield


app = FastAPI(
    title="InfraGuard AI Backend",
    description="Infrastructure anomaly detection and failure prediction API.",
    version="0.1.0",
    redirect_slashes=False,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(anomaly_router)
app.include_router(diagnose_router)
app.include_router(ai_router)
app.include_router(upload_router)
app.include_router(history_router)
app.include_router(report_router)
app.include_router(model_router)
app.include_router(live_router)

if EDA_DIR.exists():
    app.mount("/eda-assets", StaticFiles(directory=EDA_DIR), name="eda-assets")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = perf_counter()
    path = request.url.path

    if request_too_large(request):
        runtime_metrics.record_invalid_request()
        logger.warning(
            "request rejected: payload too large",
            extra={"method": request.method, "path": path},
        )
        return JSONResponse(
            status_code=413,
            content={"error": "Payload too large"},
            headers=security_headers(),
        )

    if not authenticated(request):
        runtime_metrics.record_invalid_request()
        logger.warning(
            "request rejected: invalid api key",
            extra={"method": request.method, "path": path},
        )
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized"},
            headers=security_headers(),
        )

    allowed, limit = check_rate_limit(request)
    if not allowed:
        logger.warning(
            "request rejected: rate limit exceeded",
            extra={"method": request.method, "path": path, "rate_limit": limit},
        )
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "limit": f"{limit} requests per minute"},
            headers=security_headers(),
        )

    logger.info(
        "request received",
        extra={"endpoint": path, "method": request.method},
    )
    response = await call_next(request)
    duration_ms = round((perf_counter() - start_time) * 1000, 2)
    runtime_metrics.record_request(duration_ms)
    logger.info(
        "request completed",
        extra={
            "endpoint": path,
            "method": request.method,
            "status_code": response.status_code,
            "response_time_ms": duration_ms,
        },
    )
    for header, value in security_headers().items():
        response.headers[header] = value
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    path = request.url.path.rstrip("/") or "/"
    if exc.status_code == 405 and path in {"/predict", "/anomaly"}:
        logger.warning(
            "method not allowed",
            extra={"method": request.method, "endpoint": request.url.path},
        )
        return JSONResponse(
            status_code=405,
            content={"error": "Method not allowed. Use POST."},
        )

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(
        "invalid request payload",
        extra={"method": request.method, "endpoint": request.url.path, "errors": exc.errors()},
    )
    runtime_metrics.record_invalid_request()
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request payload"},
    )


@app.get("/", tags=["health"])
def root() -> dict[str, object]:
    return {
        "service": "InfraGuard AI Backend",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "predict": "POST /predict",
            "anomaly": "POST /anomaly",
            "diagnose": "POST /diagnose",
            "ai_analyze": "POST /ai/analyze",
            "ai_what_if": "POST /ai/what-if",
            "nova_briefing": "GET /ai/nova/briefing",
            "upload": "POST /upload",
            "history": "GET /history",
            "report": "GET /report",
            "model_info": "GET /model-info",
            "eda": "GET /eda",
            "benchmark_report": "GET /benchmark-report",
            "live_status": "GET /live/status",
            "live_tick": "POST /live/tick",
        },
    }


@app.get("/health", tags=["health"], response_model=HealthResponse)
def health() -> HealthResponse:
    db_connected = check_database()
    service = get_ml_service()
    metrics = runtime_metrics.snapshot()
    healthy = db_connected and service.models_loaded()
    return HealthResponse(
        status="healthy" if healthy else "degraded",
        service="InfraGuard AI",
        uptime_seconds=float(metrics["uptime_seconds"]),
        ml_models_loaded=service.models_loaded(),
        db_connected=db_connected,
        metrics=metrics,
    )
