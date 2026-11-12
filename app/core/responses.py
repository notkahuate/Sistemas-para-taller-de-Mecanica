"""Envelope estándar de respuesta (Componente G del Parcial #2).

Toda respuesta del API tiene exactamente estos campos:
success, message, data, errors, timestamp, traceId.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

ZONA_BOGOTA = timezone(timedelta(hours=-5))


def ahora_bogota() -> datetime:
    """Fecha y hora actual con offset -05:00, sin microsegundos."""
    return datetime.now(ZONA_BOGOTA).replace(microsecond=0)


def a_iso_bogota(valor: datetime) -> str:
    """Convierte una fecha-hora a ISO-8601 con offset -05:00.

    SQLite guarda las fechas sin zona horaria; si llega sin zona se asume hora de Bogotá.
    """
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=ZONA_BOGOTA)
    return valor.astimezone(ZONA_BOGOTA).replace(microsecond=0).isoformat()


def nuevo_trace_id() -> str:
    return f"mts-{uuid.uuid4().hex[:6]}"


def envelope(
    *,
    success: bool,
    message: str,
    data: Any = None,
    errors: list[dict] | None = None,
    status_code: int = 200,
) -> JSONResponse:
    contenido = {
        "success": success,
        "message": message,
        "data": jsonable_encoder(data),
        "errors": errors or [],
        "timestamp": a_iso_bogota(ahora_bogota()),
        "traceId": nuevo_trace_id(),
    }
    return JSONResponse(status_code=status_code, content=contenido)
