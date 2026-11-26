"""Entidad Orden de servicio y estados del ciclo de atención (FUN-16)."""
import re
from dataclasses import dataclass
from datetime import datetime

ESTADO_RECIBIDA = "recibida"
ESTADO_EN_PROCESO = "en_proceso"
ESTADO_FINALIZADA = "finalizada"
ESTADOS_ABIERTOS = (ESTADO_RECIBIDA, ESTADO_EN_PROCESO)

ID_MOTOCICLETA_RE = re.compile(r"^MTO-\d{4}$")
ID_ORDEN_RE = re.compile(r"^OS-\d{4}$")
ID_ESPECIALIDAD_RE = re.compile(r"^ESP-[A-Z]{3}$")


@dataclass
class OrdenServicio:
    id_orden: str
    id_cliente: str
    id_motocicleta: str
    id_cita: str | None
    motivo_visita: str
    estado: str
    fecha_ingreso: datetime
    observaciones: str | None
    id_tecnico: str | None
    id_especialidad_requerida: str | None = None
    fecha_asignacion: datetime | None = None
    fecha_cierre: datetime | None = None


def generar_id_orden(secuencia: int) -> str:
    """El idOrden lo genera el sistema: prefijo OS- y secuencia de 4 dígitos."""
    return f"OS-{secuencia:04d}"
