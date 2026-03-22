from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.router import router
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Backend Service", version="0.1.0")
    register_exception_handlers(app)
    app.include_router(router, prefix="/api")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
