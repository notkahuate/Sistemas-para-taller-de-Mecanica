"""Contratos JSON de inventario (camelCase, como en el Parcial #2)."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def cantidad_json(valor: Decimal) -> int | float:
    """Cantidades de inventario: número entero si no tiene decimales, si no hasta 3 decimales."""
    valor = valor.quantize(Decimal("0.001"))
    return int(valor) if valor == valor.to_integral_value() else float(valor)


class EntradaStockCrear(BaseModel):
    """Body de POST /api/v1/inventario/entradas."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "referencia": "PAS-FZ150",
                "cantidad": 10,
                "idRecepcion": None,
                "ubicacion": "EST-A-03",
                "motivo": "ajuste_positivo",
            }
        },
    )

    referencia: str = Field(max_length=40)
    cantidad: Decimal = Field(max_digits=14)
    id_recepcion: str | None = Field(default=None, alias="idRecepcion")
    ubicacion: str | None = Field(default=None, max_length=30)
    motivo: str = Field(max_length=30)


class EntradaStockRegistrada(BaseModel):
    """data de la respuesta de HU-037."""

    model_config = ConfigDict(from_attributes=True)

    id_movimiento: str = Field(serialization_alias="idMovimiento")
    tipo: str
    referencia: str
    cantidad: Decimal
    stock_resultante: Decimal = Field(serialization_alias="stockResultante")
    id_recepcion: str | None = Field(serialization_alias="idRecepcion")

    @field_serializer("cantidad", "stock_resultante")
    def _cantidad(self, valor: Decimal) -> int | float:
        return cantidad_json(valor)
