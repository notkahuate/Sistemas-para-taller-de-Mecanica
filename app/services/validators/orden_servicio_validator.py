"""Validaciones de formato de una orden de servicio (FUN-16 y FUN-17)."""
from app.domain.entities.cliente import ID_CLIENTE_RE
from app.domain.entities.orden_servicio import ID_ESPECIALIDAD_RE, ID_MOTOCICLETA_RE, ID_ORDEN_RE
from app.domain.entities.tecnico import ID_TECNICO_RE


def validar_formato_orden(datos: dict) -> list[tuple[str, str, str]]:
    """Devuelve una lista de (campo, código, detalle) con cada dato que no cumple el contrato."""
    errores: list[tuple[str, str, str]] = []
    if not datos["motivo_visita"].strip():
        errores.append(("motivoVisita", "VAL-REQUERIDO", "MotivoVisita vacío"))
    if not ID_CLIENTE_RE.match(datos["id_cliente"]):
        errores.append(("idCliente", "VAL-FORMATO", "Formato de idCliente no válido. Debe ser CLI-NNNN."))
    if not ID_MOTOCICLETA_RE.match(datos["id_motocicleta"]):
        errores.append(("idMotocicleta", "VAL-FORMATO", "Formato de idMotocicleta no válido. Debe ser MTO-NNNN."))
    if datos.get("id_cita") is not None:
        errores.append(
            ("idCita", "VAL-FORMATO", "El módulo de citas no está disponible en esta versión; envíe idCita en null.")
        )
    return errores


def validar_formato_asignacion(id_orden: str, datos: dict) -> list[tuple[str, str, str]]:
    """HU-017: formato del idOrden de la ruta y del body de la asignación."""
    errores: list[tuple[str, str, str]] = []
    if not ID_ORDEN_RE.match(id_orden):
        errores.append(("idOrden", "VAL-FORMATO", "Formato de idOrden no válido. Debe ser OS-NNNN."))
    if not ID_TECNICO_RE.match(datos["id_tecnico"]):
        errores.append(("idTecnico", "VAL-FORMATO", "Formato de idTecnico no válido. Debe ser TEC-NNNN."))
    especialidad = datos.get("id_especialidad_requerida")
    if especialidad is not None and not ID_ESPECIALIDAD_RE.match(especialidad):
        errores.append(
            ("idEspecialidadRequerida", "VAL-FORMATO", "Formato de idEspecialidadRequerida no válido. Debe ser ESP-XXX.")
        )
    if datos["fecha_asignacion"].tzinfo is None:
        errores.append(("fechaAsignacion", "VAL-FORMATO", "fechaAsignacion debe incluir el offset, por ejemplo -05:00."))
    return errores
