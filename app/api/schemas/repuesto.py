"""Contratos JSON de repuestos (camelCase, como en el Parcial #2)."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer


class RepuestoCrear(BaseModel):
    """Body de POST /api/v1/repuestos. El estado, el idRepuesto y el stock los pone el sistema."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "referencia": "PAS-FZ150",
                "nombre": "Pastillas freno delantero FZ 150",
                "descripcion": "Juego original",
                "idCategoria": "CAT-FRE",
                "idProveedor": "PRV-08",
                "costo": 28000.0,
                "precio": 45000.0,
                "stockMinimo": 2,
            }
        },
    )

    referencia: str = Field(max_length=40)
    nombre: str = Field(max_length=120)
    descripcion: str | None = Field(default=None, max_length=300)
    id_categoria: str = Field(alias="idCategoria", max_length=10)
    id_proveedor: str | None = Field(default=None, alias="idProveedor", max_length=20)
    costo: Decimal = Field(max_digits=12, decimal_places=2)
    precio: Decimal = Field(max_digits=12, decimal_places=2)
    stock_minimo: int = Field(alias="stockMinimo")


class RepuestoRegistrado(BaseModel):
    """data de la respuesta de HU-031."""

    model_config = ConfigDict(from_attributes=True)

    id_repuesto: str = Field(serialization_alias="idRepuesto")
    referencia: str
    estado: str
    costo: Decimal
    precio: Decimal

    @computed_field(alias="stockDisponible")
    @property
    def stock_disponible(self) -> int:
        # Un repuesto recién registrado no tiene movimientos de inventario.
        return 0

    @field_serializer("costo", "precio")
    def _dinero(self, valor: Decimal) -> float:
        return float(round(valor, 2))
