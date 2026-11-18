"""Validaciones de formato de un técnico (FUN-76)."""
from datetime import date

from app.domain.entities.cliente import CORREO_RE, DOCUMENTO_RE, TELEFONO_RE, TIPOS_DOCUMENTO


def validar_formato_tecnico(datos: dict, hoy: date) -> list[tuple[str, str]]:
    """Devuelve una lista de (campo, detalle) con cada dato que no cumple el contrato."""
    errores: list[tuple[str, str]] = []
    if datos["tipo_documento"] not in TIPOS_DOCUMENTO:
        errores.append(("tipoDocumento", "Tipo de documento no válido. Use CC, CE, NIT o PAS."))
    if not DOCUMENTO_RE.match(datos["numero_documento"]):
        errores.append(("numeroDocumento", "El número de documento debe tener entre 6 y 15 caracteres alfanuméricos."))
    if not datos["nombre_completo"].strip():
        errores.append(("nombreCompleto", "El nombre completo es obligatorio."))
    if not TELEFONO_RE.match(datos["telefono"]):
        errores.append(("telefono", "Formato de teléfono no válido. Debe tener 10 dígitos e iniciar en 3 o 7."))
    if not CORREO_RE.match(datos["correo"]):
        errores.append(("correo", "Formato de correo no válido."))
    if not datos["cargo"].strip():
        errores.append(("cargo", "El cargo es obligatorio."))
    if datos["fecha_ingreso"] > hoy:
        errores.append(("fecha", "FechaIngreso futura"))
    if datos["tarifa_horaria"] < 0:
        errores.append(("tarifaHoraria", "La tarifa horaria no puede ser negativa."))
    return errores
