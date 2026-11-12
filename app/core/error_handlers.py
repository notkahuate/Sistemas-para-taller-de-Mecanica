"""Manejadores globales de errores: siempre responden con el envelope estándar."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.responses import envelope
from app.domain.exceptions.errors import AppError

MENSAJE_BD_CAIDA = "No fue posible completar la operación por indisponibilidad de la base de datos."


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def manejar_error_app(_: Request, exc: AppError):
        return envelope(
            success=False,
            message=exc.message,
            errors=[{"campo": exc.campo, "codigo": exc.codigo, "detalle": exc.detalle}],
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def manejar_validacion(_: Request, exc: RequestValidationError):
        errores = [
            {
                "campo": ".".join(str(p) for p in e["loc"] if p != "body"),
                "codigo": "VAL-FORMATO",
                "detalle": e["msg"],
            }
            for e in exc.errors()
        ]
        return envelope(success=False, message="La solicitud tiene datos no válidos.", errors=errores, status_code=400)

    @app.exception_handler(SQLAlchemyError)
    async def manejar_error_bd(_: Request, exc: SQLAlchemyError):
        return envelope(
            success=False,
            message=MENSAJE_BD_CAIDA,
            errors=[{"campo": "persistencia", "codigo": "DB-DOWN", "detalle": "Base de datos no disponible"}],
            status_code=503,
        )
