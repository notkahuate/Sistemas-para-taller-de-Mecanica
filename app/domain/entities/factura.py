"""Entidad Factura de servicio y cálculo de totales (FUN-61, invocada desde FUN-20)."""
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

ESTADO_EMITIDA = "emitida"
ESTADO_ANULADA = "anulada"
IVA = Decimal("0.19")  # IVA 19% fijo sobre subtotal - descuentos
CENTAVOS = Decimal("0.01")


@dataclass
class Factura:
    id_factura: str
    id_orden: str
    id_cliente: str
    mano_obra: Decimal
    repuestos: Decimal
    subtotal: Decimal
    descuentos: Decimal
    base_iva: Decimal
    impuestos: Decimal
    total: Decimal
    saldo_pendiente: Decimal
    estado: str
    fecha_emision: datetime


def redondear(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def calcular_totales(mano_obra: Decimal, repuestos: Decimal, descuentos: Decimal = Decimal("0")) -> dict:
    """RN-05: mano de obra + repuestos - descuentos + IVA 19%."""
    mano_obra, repuestos, descuentos = redondear(mano_obra), redondear(repuestos), redondear(descuentos)
    subtotal = mano_obra + repuestos
    base_iva = subtotal - descuentos
    impuestos = redondear(base_iva * IVA)
    return {
        "mano_obra": mano_obra,
        "repuestos": repuestos,
        "subtotal": subtotal,
        "descuentos": descuentos,
        "base_iva": base_iva,
        "impuestos": impuestos,
        "total": base_iva + impuestos,
    }


def generar_id_factura(secuencia: int) -> str:
    """El idFactura lo genera el sistema: prefijo FAC- y secuencia de 4 dígitos."""
    return f"FAC-{secuencia:04d}"
