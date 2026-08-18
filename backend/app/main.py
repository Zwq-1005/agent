import logging
import uuid
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import UPLOAD_DIR, CORS_ORIGINS, LOG_LEVEL
from app.database import create_db_and_tables, seed_default_prompts
from app.routers import upload, session, analyze, prompts

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Create tables on startup
    create_db_and_tables()
    UPLOAD_DIR.mkdir(exist_ok=True)
    logger.info("Database tables created, upload directory ready")

    # Seed default prompt templates
    seed_default_prompts()
    logger.info("Default prompt templates seeded")

    yield


app = FastAPI(
    title="医学统计AI助手 API",
    description="Medical Statistical Analysis Platform with LLM + LangGraph AI orchestration",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ──────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

 
# ─── Request ID + Logging Middleware ───────────────────────────────────────────────

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add a unique request ID and log each request."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s %d %.1fms [%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


# ─── Global Exception Handlers ─────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found", "path": str(request.url.path)},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception("Internal server error: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc):
    logger.exception("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Unexpected error: {str(exc)}",
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


# ─── Mount Routers ─────────────────────────────────────────────────────────────────

app.include_router(upload.router)
app.include_router(session.router)
app.include_router(analyze.router)
app.include_router(prompts.router)


@app.get("/")
async def root():
    return {"message": "AI 统计分析平台 API", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
