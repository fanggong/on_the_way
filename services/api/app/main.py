from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.core.errors import AppError
from app.db.init_db import init_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    init_database()
    logger.info("database initialized")


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    request_id = exc.request_id or str(uuid4())
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "status": "error",
            "code": exc.code,
            "message": exc.message,
            "request_id": request_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = str(uuid4())
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "code": "INVALID_ARGUMENT",
            "message": str(exc),
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(_: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid4())
    logger.exception("unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_ERROR",
            "message": "unexpected server error",
            "request_id": request_id,
        },
    )
