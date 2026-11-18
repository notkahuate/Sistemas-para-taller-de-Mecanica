"""Contratos JSON de técnicos (camelCase, como en el Parcial #2)."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TecnicoCrear(BaseModel):
    """Body de POST /api/v1/tecnicos. El estado y el idTecnico los pone el sistema."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "tipoDocumento": "CC",
                "numeroDocumento": "109111222",
                "nombreCompleto": "Luis Martínez",
                "telefono": "3002223344",
                "correo": "luis.martinez@motoservice.com",
                "cargo": "Técnico de frenos",
                "fechaIngreso": "2026-02-01",
                "tarifaHoraria": 40000.0,
            }
        },
    )

    tipo_documento: str = Field(alias="tipoDocumento")
    numero_documento: str = Field(alias="numeroDocumento")
    nombre_completo: str = Field(alias="nombreCompleto", max_length=120)
    telefono: str
    correo: str = Field(max_length=120)
    cargo: str = Field(max_length=80)
    fecha_ingreso: date = Field(alias="fechaIngreso")
    tarifa_horaria: Decimal = Field(alias="tarifaHoraria", max_digits=12, decimal_places=2)


class TecnicoRegistrado(BaseModel):
    """data de la respuesta de HU-076."""

    model_config = ConfigDict(from_attributes=True)

    id_tecnico: str = Field(serialization_alias="idTecnico")
    numero_documento: str = Field(serialization_alias="numeroDocumento")
    nombre_completo: str = Field(serialization_alias="nombreCompleto")
    estado: str
    tarifa_horaria: Decimal = Field(serialization_alias="tarifaHoraria")
    fecha_ingreso: date = Field(serialization_alias="fechaIngreso")

    @field_serializer("tarifa_horaria")
    def _dinero(self, valor: Decimal) -> float:
        return float(round(valor, 2))

    @field_serializer("fecha_ingreso")
    def _fecha(self, valor: date) -> str:
        return valor.isoformat()
