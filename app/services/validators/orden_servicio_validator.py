"""Validaciones de formato de una orden de servicio (FUN-16)."""
from app.domain.entities.cliente import ID_CLIENTE_RE
from app.domain.entities.orden_servicio import ID_MOTOCICLETA_RE


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
