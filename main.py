from fastapi import FastAPI

from app.api.routers import health
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG,
)

app.include_router(health.router)
