from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.exception_handlers import register_exception_handlers
from app.api.router import router
from app.core.config import settings
from app.core.kimi_client import close_kimi_client
from app.core.logging import setup_logging
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    close_kimi_client()


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Backend Service", version="0.1.0", lifespan=lifespan)
    register_exception_handlers(app)
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(router, prefix="/api")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get(
        "/health/ready",
        responses={503: {"description": "数据库不可达或连接失败"}},
    )
    def health_ready() -> dict:
        """进程已启动且数据库可连通时返回 200，否则 503（编排/探针用）。"""
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 — 探针需吞掉驱动差异
            raise HTTPException(
                status_code=503,
                detail={"status": "degraded", "database": False, "reason": str(exc)},
            ) from exc
        finally:
            db.close()
        return {"status": "ok", "database": True}

    return app


app = create_app()
