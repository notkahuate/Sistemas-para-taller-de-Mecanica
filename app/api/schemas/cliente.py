"""Contratos JSON de clientes (camelCase, como en el Parcial #2)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.responses import a_iso_bogota


class ClienteCrear(BaseModel):
    """Body de POST /api/v1/clientes. No acepta estado ni idCliente: los pone el sistema."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "tipoDocumento": "CC",
                "numeroDocumento": "1098765432",
                "nombreCompleto": "Carlos Andrés Pérez Gómez",
                "telefono": "3001234567",
                "correo": "carlos.perez@email.com",
                "direccion": "Calle 45 # 12-30, Bucaramanga",
            }
        },
    )

    tipo_documento: str = Field(alias="tipoDocumento")
    numero_documento: str = Field(alias="numeroDocumento")
    nombre_completo: str = Field(alias="nombreCompleto", max_length=120)
    telefono: str
    correo: str = Field(max_length=120)
    direccion: str = Field(max_length=200)


class ClienteRegistrado(BaseModel):
    """data de la respuesta de HU-001."""

    model_config = ConfigDict(from_attributes=True)

    id_cliente: str = Field(serialization_alias="idCliente")
    tipo_documento: str = Field(serialization_alias="tipoDocumento")
    numero_documento: str = Field(serialization_alias="numeroDocumento")
    nombre_completo: str = Field(serialization_alias="nombreCompleto")
    telefono: str
    correo: str
    direccion: str
    estado: str
    fecha_registro: datetime = Field(serialization_alias="fechaRegistro")

    @field_serializer("fecha_registro")
    def _fecha_iso(self, valor: datetime) -> str:
        return a_iso_bogota(valor)
