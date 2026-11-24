"""Entidad Actividad de mantenimiento ejecutada sobre una orden de servicio (FUN-26)."""
from dataclasses import dataclass
from datetime import datetime

ESTADO_PENDIENTE = "pendiente"
ESTADO_EN_EJECUCION = "en_ejecucion"
ESTADO_COMPLETADA = "completada"
ESTADOS_ACTIVIDAD = (ESTADO_PENDIENTE, ESTADO_EN_EJECUCION, ESTADO_COMPLETADA)

NOMBRE_MIN, NOMBRE_MAX = 5, 200
TOLERANCIA_HORA_INICIO_MIN = 10  # horaInicio <= ahora + 10 minutos


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


def generar_id_actividad(secuencia: int) -> str:
    """El idActividad lo genera el sistema: prefijo ACT- y secuencia de 4 dígitos."""
    return f"ACT-{secuencia:04d}"
