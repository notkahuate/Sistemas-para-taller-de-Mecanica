"""Validaciones de formato de una motocicleta (FUN-06)."""
from app.domain.entities.motocicleta import (
    ANIO_MINIMO,
    CILINDRAJE_MAXIMO,
    CILINDRAJE_MINIMO,
    PLACA_RE,
    VIN_RE,
    anio_maximo,
)
from app.domain.entities.cliente import ID_CLIENTE_RE


def validar_formato_motocicleta(datos: dict) -> list[tuple[str, str]]:
    """Devuelve una lista de (campo, detalle) con cada dato que no cumple el formato."""
    errores: list[tuple[str, str]] = []
    if not PLACA_RE.match(datos["placa"]):
        errores.append(("placa", "Placa con formato inválido"))
    if datos.get("vin") is not None and not VIN_RE.match(datos["vin"]):
        errores.append(("vin", "VIN con formato inválido. Debe tener 17 caracteres o enviarse como null."))
    if not datos["marca"].strip():
        errores.append(("marca", "La marca es obligatoria."))
    if not datos["linea"].strip():
        errores.append(("linea", "La línea es obligatoria."))
    if not ANIO_MINIMO <= datos["anio"] <= anio_maximo():
        errores.append(("anio", f"El año debe estar entre {ANIO_MINIMO} y {anio_maximo()}."))
    if not CILINDRAJE_MINIMO <= datos["cilindraje"] <= CILINDRAJE_MAXIMO:
        errores.append(("cilindraje", f"El cilindraje debe estar entre {CILINDRAJE_MINIMO} y {CILINDRAJE_MAXIMO}."))
    if not datos["color"].strip():
        errores.append(("color", "El color es obligatorio."))
    if not ID_CLIENTE_RE.match(datos["id_cliente"]):
        errores.append(("idCliente", "Formato de idCliente no válido. Debe ser CLI-NNNN."))
    return errores
