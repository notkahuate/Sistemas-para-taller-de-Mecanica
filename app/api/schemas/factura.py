"""Contratos JSON de facturas de servicio (camelCase, como en el Parcial #2)."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.responses import a_iso_bogota


class FacturaGenerar(BaseModel):
    """Body de POST /api/v1/facturas (HU-061)."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={"example": {"idOrden": "OS-0001", "correoEnvio": "carlos.perez@email.com"}},
    )

    id_orden: str = Field(alias="idOrden")
    correo_envio: str = Field(alias="correoEnvio", max_length=120)


class FacturaGenerada(BaseModel):
    """data de la respuesta de HU-061."""

    model_config = ConfigDict(from_attributes=True)

    id_factura: str = Field(serialization_alias="idFactura")
    id_orden: str = Field(serialization_alias="idOrden")
    id_cliente: str = Field(serialization_alias="idCliente")
    mano_obra: Decimal = Field(serialization_alias="manoObra")
    repuestos: Decimal
    subtotal: Decimal
    descuentos: Decimal
    base_iva: Decimal = Field(serialization_alias="baseIva")
    impuestos: Decimal
    total: Decimal
    saldo_pendiente: Decimal = Field(serialization_alias="saldoPendiente")
    estado: str
    fecha_emision: datetime = Field(serialization_alias="fechaEmision")

    @field_serializer(
        "mano_obra", "repuestos", "subtotal", "descuentos", "base_iva", "impuestos", "total", "saldo_pendiente"
    )
    def _dinero(self, valor: Decimal) -> float:
        return float(valor.quantize(Decimal("0.01")))

    @field_serializer("fecha_emision")
    def _fecha(self, valor: datetime) -> str:
        return a_iso_bogota(valor)
