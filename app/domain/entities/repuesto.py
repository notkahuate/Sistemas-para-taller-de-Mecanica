"""Entidad Repuesto y catálogo de categorías (FUN-31)."""
import re
from dataclasses import dataclass
from decimal import Decimal

ESTADO_ACTIVO = "activo"
REFERENCIA_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{2,29}$")

# Categorías fijas del MVP (refinamiento): el catálogo editable queda para una versión posterior.
CATEGORIAS = {
    "CAT-MOT": "Motor",
    "CAT-FRE": "Frenos",
    "CAT-ELE": "Eléctrico",
    "CAT-TRA": "Transmisión",
    "CAT-SUS": "Suspensión",
    "CAT-OTR": "Otros",
}


@dataclass
class Repuesto:
    id_repuesto: str
    referencia: str
    nombre: str
    descripcion: str | None
    id_categoria: str
    id_proveedor: str | None
    costo: Decimal
    precio: Decimal
    stock_minimo: int
    estado: str


def generar_id_repuesto(secuencia: int) -> str:
    """El idRepuesto lo genera el sistema: prefijo REP- y secuencia de 4 dígitos."""
    return f"REP-{secuencia:04d}"
