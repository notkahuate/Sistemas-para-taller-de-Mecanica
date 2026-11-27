"""Entidad Pago de cliente sobre una factura de servicio (FUN-66)."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

METODOS_PAGO = ("efectivo", "transferencia", "tarjeta", "otros")
REFERENCIA_MAX = 40


@dataclass
class PagoCliente:
    id_pago: str
    id_factura: str
    valor: Decimal
    fecha_pago: date
    metodo: str
    referencia_comprobante: str


def generar_id_pago(secuencia: int) -> str:
    """El idPago lo genera el sistema: prefijo PAG- y secuencia de 4 dígitos."""
    return f"PAG-{secuencia:04d}"
