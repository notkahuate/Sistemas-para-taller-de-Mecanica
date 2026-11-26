"""Entidad Actividad de mantenimiento ejecutada sobre una orden de servicio (FUN-26)."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

ESTADO_PENDIENTE = "pendiente"
ESTADO_EN_EJECUCION = "en_ejecucion"
ESTADO_COMPLETADA = "completada"
ESTADOS_ACTIVIDAD = (ESTADO_PENDIENTE, ESTADO_EN_EJECUCION, ESTADO_COMPLETADA)

NOMBRE_MIN, NOMBRE_MAX = 5, 200
TOLERANCIA_HORA_INICIO_MIN = 10  # horaInicio <= ahora + 10 minutos
MINUTOS_MIN, MINUTOS_MAX = 5, 480  # mano de obra por actividad (FUN-30)


@dataclass
class ActividadMantenimiento:
    id_actividad: str
    id_orden: str
    id_tecnico: str
    nombre: str
    estado: str
    observaciones: str | None
    hora_inicio: datetime
    hora_fin: datetime | None
    minutos: int | None = None
    tarifa_horaria: Decimal | None = None
    valor_mano_obra: Decimal | None = None


def generar_id_actividad(secuencia: int) -> str:
    """El idActividad lo genera el sistema: prefijo ACT- y secuencia de 4 dígitos."""
    return f"ACT-{secuencia:04d}"
