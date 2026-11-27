"""Contratos JSON de facturas de servicio (camelCase, como en el Parcial #2)."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.api.schemas.inventario import cantidad_json
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


class ManoObraDetalle(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_actividad: str = Field(serialization_alias="idActividad")
    minutos: int
    valor: Decimal = Field(validation_alias="valor_mano_obra")

    @field_serializer("valor")
    def _valor(self, valor: Decimal) -> float:
        return float(valor.quantize(Decimal("0.01")))


class RepuestoDetalle(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    referencia: str
    cantidad: Decimal
    precio: Decimal = Field(validation_alias="precio_unitario")

    @field_serializer("cantidad")
    def _cantidad(self, valor: Decimal) -> int | float:
        return cantidad_json(valor)

    @field_serializer("precio")
    def _precio(self, valor: Decimal) -> float:
        return float(valor.quantize(Decimal("0.01")))


class DetalleFactura(BaseModel):
    mano_obra: list[ManoObraDetalle] = Field(serialization_alias="manoObra")
    repuestos: list[RepuestoDetalle]


class FacturaConsultada(BaseModel):
    """data de la respuesta de HU-062."""

    id_factura: str = Field(serialization_alias="idFactura")
    id_orden: str = Field(serialization_alias="idOrden")
    id_cliente: str = Field(serialization_alias="idCliente")
    estado: str
    total: Decimal
    saldo_pendiente: Decimal = Field(serialization_alias="saldoPendiente")
    pagos: list[dict]
    detalle: DetalleFactura

    @field_serializer("total", "saldo_pendiente")
    def _dinero(self, valor: Decimal) -> float:
        return float(valor.quantize(Decimal("0.01")))
