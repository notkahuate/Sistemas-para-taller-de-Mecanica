"""Validaciones de formato de una actividad de mantenimiento (FUN-26)."""
from datetime import timedelta

from app.core.responses import ahora_bogota
from app.domain.entities.actividad_mantenimiento import (
    ESTADOS_ACTIVIDAD,
    NOMBRE_MAX,
    NOMBRE_MIN,
    TOLERANCIA_HORA_INICIO_MIN,
)
from app.domain.entities.orden_servicio import ID_ORDEN_RE


def validar_formato_actividad(id_orden: str, datos: dict) -> list[tuple[str, str, str]]:
    """Devuelve una lista de (campo, código, detalle) con cada dato que no cumple el contrato."""
    errores: list[tuple[str, str, str]] = []
    if not ID_ORDEN_RE.match(id_orden):
        errores.append(("idOrden", "VAL-FORMATO", "Formato de idOrden no válido. Debe ser OS-NNNN."))
    nombre = datos["nombre"].strip()
    if not nombre:
        errores.append(("nombre", "VAL-REQUERIDO", "Nombre vacío"))
    elif not NOMBRE_MIN <= len(nombre) <= NOMBRE_MAX:
        errores.append(("nombre", "VAL-FORMATO", f"El nombre debe tener entre {NOMBRE_MIN} y {NOMBRE_MAX} caracteres."))
    if datos["estado"] not in ESTADOS_ACTIVIDAD:
        errores.append(("estado", "VAL-FORMATO", "Estado no válido. Use pendiente, en_ejecucion o completada."))
    hora = datos["hora_inicio"]
    if hora.tzinfo is None:
        errores.append(("horaInicio", "VAL-FORMATO", "horaInicio debe incluir el offset, por ejemplo -05:00."))
    elif hora > ahora_bogota() + timedelta(minutes=TOLERANCIA_HORA_INICIO_MIN):
        errores.append(("horaInicio", "VAL-FORMATO", "horaInicio no puede ser posterior a la hora actual más 10 minutos."))
    return errores
