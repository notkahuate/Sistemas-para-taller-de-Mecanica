"""Movimiento de inventario: bitácora única de la que sale el stock (FUN-37, absorbe FUN-41)."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

TIPO_ENTRADA = "ENTRADA"
TIPO_SALIDA = "SALIDA"
MOTIVOS_ENTRADA = ("recepcion_compra", "ajuste_positivo", "devolucion_cliente")


@dataclass
class MovimientoInventario:
    id_movimiento: str
    id_repuesto: str
    referencia: str
    tipo: str
    motivo: str
    cantidad: Decimal
    stock_resultante: Decimal
    id_recepcion: str | None
    ubicacion: str | None
    usuario: str
    fecha: datetime


def generar_id_movimiento(secuencia: int) -> str:
    """El idMovimiento lo genera el sistema: prefijo MOV- y secuencia de 4 dígitos."""
    return f"MOV-{secuencia:04d}"
