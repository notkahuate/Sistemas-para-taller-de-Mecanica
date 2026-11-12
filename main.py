from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.domain import models as _modelos  # noqa: F401  (registra las tablas en Base.metadata)
from app.api.routers import health
from app.core.config import settings
from app.core.database import Base, engine
from app.core.error_handlers import registrar_manejadores


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Crea las tablas que falten al arrancar (en desarrollo, mientras no usemos migraciones de Alembic).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

registrar_manejadores(app)

app.include_router(health.router)
