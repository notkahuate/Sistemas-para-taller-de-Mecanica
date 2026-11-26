"""Esquemas de entrada y salida de HU-027 Registrar repuestos utilizados."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.api.schemas.inventario import cantidad_json


class ConsumoCrear(BaseModel):
    """Body de POST /api/v1/ordenes-servicio/{idOrden}/repuestos-utilizados."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {"idActividad": "ACT-0001", "referencia": "PAS-FZ150", "cantidad": 1, "motivo": "consumo_orden"}
        },
    )

    id_actividad: str = Field(alias="idActividad")
    referencia: str = Field(max_length=40)
    cantidad: Decimal = Field(max_digits=14)
    motivo: str = Field(max_length=30)


class ConsumoRegistrado(BaseModel):
    """data de la respuesta de HU-027."""

    model_config = ConfigDict(from_attributes=True)

    id_consumo: str = Field(serialization_alias="idConsumo")
    id_orden: str = Field(serialization_alias="idOrden")
    id_actividad: str = Field(serialization_alias="idActividad")
    referencia: str
    cantidad: Decimal
    stock_resultante: Decimal = Field(serialization_alias="stockResultante")
    precio_unitario: Decimal = Field(serialization_alias="precioUnitario")
    id_movimiento: str = Field(serialization_alias="idMovimiento")

    @field_serializer("cantidad", "stock_resultante")
    def _cantidades(self, valor: Decimal) -> int | float:
        return cantidad_json(valor)

    @field_serializer("precio_unitario")
    def _precio(self, valor: Decimal) -> float:
        return float(valor.quantize(Decimal("0.01")))
