"""Contratos JSON de pagos de clientes (camelCase, como en el Parcial #2)."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.domain.entities.pago_cliente import REFERENCIA_MAX


class PagoClienteCrear(BaseModel):
    """Body de POST /api/v1/pagos/clientes (HU-066)."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "idFactura": "FAC-0001",
                "valor": 141312.5,
                "fechaPago": "2026-10-14",
                "metodo": "transferencia",
                "referenciaComprobante": "TRX-445566",
            }
        },
    )

    id_factura: str = Field(alias="idFactura")
    valor: Decimal = Field(max_digits=14)
    fecha_pago: date = Field(alias="fechaPago")
    metodo: str = Field(max_length=15)
    referencia_comprobante: str = Field(alias="referenciaComprobante", max_length=REFERENCIA_MAX)


class PagoClienteRegistrado(BaseModel):
    """data de la respuesta de HU-066."""

    id_pago: str = Field(serialization_alias="idPago")
    id_factura: str = Field(serialization_alias="idFactura")
    valor: Decimal
    saldo_pendiente: Decimal = Field(serialization_alias="saldoPendiente")
    estado_factura: str = Field(serialization_alias="estadoFactura")
    metodo: str
    referencia_comprobante: str = Field(serialization_alias="referenciaComprobante")

    @field_serializer("valor", "saldo_pendiente")
    def _dinero(self, valor: Decimal) -> float:
        return float(valor.quantize(Decimal("0.01")))
