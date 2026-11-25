"""Entidad Consumo de repuesto en una orden de servicio (FUN-27)."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

MOTIVO_CONSUMO_ORDEN = "consumo_orden"  # el movimiento queda como SALIDA con este motivo (SALIDA_CONSUMO)


@dataclass
class ConsumoRepuesto:
    id_consumo: str
    id_orden: str
    id_actividad: str
    id_repuesto: str
    referencia: str
    cantidad: Decimal
    precio_unitario: Decimal
    id_movimiento: str
    stock_resultante: Decimal
    usuario: str
    fecha: datetime


def generar_id_consumo(secuencia: int) -> str:
    """El idConsumo lo genera el sistema: prefijo CON- y secuencia de 4 dígitos."""
    return f"CON-{secuencia:04d}"
