from contextlib import asynccontextmanager
import json
import logging

import firebase_admin
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from firebase_admin import credentials
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.limiter import limiter
from app.scheduler import start_scheduler, stop_scheduler
from app.ws.handler import ws_router

logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.2,
    )

docs_url = "/docs" if settings.ENVIRONMENT == "development" else None
redoc_url = "/redoc" if settings.ENVIRONMENT == "development" else None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.FIREBASE_CREDENTIALS_JSON.strip():
        try:
            cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
            cred = credentials.Certificate(cred_dict)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin inicialitzat correctament")
        except Exception as e:
            logger.warning("Firebase Admin no inicialitzat: %s", e)

    if settings.SCHEDULER_ENABLED:
        start_scheduler()

    yield

    if settings.SCHEDULER_ENABLED:
        stop_scheduler()


app = FastAPI(
    title="Lists API",
    version="0.1.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Too many requests"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
