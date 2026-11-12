from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.domain import models as _modelos  # noqa: F401  (registra las tablas en Base.metadata)
from app.api.routers import auth, clientes, health
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.error_handlers import registrar_manejadores
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Crea las tablas que falten al arrancar (en desarrollo, mientras no usemos migraciones de Alembic).
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        AuthService(UsuarioRepository(db)).crear_usuarios_iniciales()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

registrar_manejadores(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(clientes.router)
