from __future__ import annotations

import utils.clients
import utils.http_session
import utils.transport
import utils.session
import time
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api import api_router
from app.config import get_settings
from app.database import init_db
from app.logging import configure_logging, get_logger
from app.metrics import http_request_duration, http_requests_total, render_metrics

settings = get_settings()
configure_logging()
logger = get_logger("fieldops")

app = FastAPI(
    title="FieldOps AI",
    description=(
        "AI-assisted field operations intelligence platform: offline-first mobile data collection, "
        "deterministic risk assessment, Gemini-powered contextual analysis, operational analytics, "
        "and production observability."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    started = time.perf_counter()
    path = request.url.path
    template = path
    for prefix in ("/api/v1/inspections/", "/api/v1/assets/", "/api/v1/work-orders/", "/api/v1/media/"):
        if path.startswith(prefix) and len(path) > len(prefix):
            template = prefix + "{id}"
            break
    try:
        response = await call_next(request)
    except Exception:
        http_requests_total.labels(request.method, template, "500").inc()
        raise
    elapsed = time.perf_counter() - started
    http_requests_total.labels(request.method, template, str(response.status_code)).inc()
    http_request_duration.labels(request.method, template).observe(elapsed)
    return response


@app.on_event("startup")
async def startup() -> None:
    await init_db()
    if settings.seed_demo_data:
        from app.seed import seed_if_needed

        await seed_if_needed()
    logger.info("fieldops_started", env=settings.app_env, database=settings.database_url.split("://")[0])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "fieldops-ai", "version": "1.0.0"}


@app.get("/ready")
async def ready() -> dict:
    from sqlalchemy import text
    from app.database import engine

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.get("/metrics")
async def metrics() -> Response:
    if not settings.prometheus_enabled:
        return JSONResponse({"detail": "metrics disabled"}, status_code=404)
    payload, content_type = render_metrics()
    return PlainTextResponse(payload.decode("utf-8"), media_type=content_type)


app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict:
    return {
        "name": "FieldOps AI",
        "tagline": "Turn field observations into structured operational intelligence.",
        "docs": "/docs",
        "health": "/health",
        "principle": "AI assists decision-making; AI does not control critical business rules.",
    }
