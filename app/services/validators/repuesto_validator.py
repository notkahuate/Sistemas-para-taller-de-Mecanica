"""Validaciones de formato de un repuesto (FUN-31)."""
from app.domain.entities.repuesto import REFERENCIA_RE


def validar_formato_repuesto(datos: dict) -> list[tuple[str, str]]:
    """Devuelve una lista de (campo, detalle) con cada dato que no cumple el contrato."""
    errores: list[tuple[str, str]] = []
    if not REFERENCIA_RE.match(datos["referencia"]):
        errores.append(("referencia", "La referencia debe tener entre 3 y 30 caracteres alfanuméricos."))
    if not datos["nombre"].strip():
        errores.append(("nombre", "El nombre es obligatorio."))
    if datos["costo"] < 0:
        errores.append(("costo", "El costo no puede ser negativo."))
    if datos["precio"] < 0:
        errores.append(("precio", "El precio no puede ser negativo."))
    if datos["costo"] >= 0 and datos["precio"] >= 0 and datos["precio"] < datos["costo"]:
        errores.append(("request", "Precio menor que costo"))
    if datos["stock_minimo"] < 0:
        errores.append(("stockMinimo", "El stock mínimo no puede ser negativo."))
    return errores
