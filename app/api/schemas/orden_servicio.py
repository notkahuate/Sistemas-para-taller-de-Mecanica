"""Contratos JSON de órdenes de servicio (camelCase, como en el Parcial #2)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.responses import a_iso_bogota


class OrdenServicioCrear(BaseModel):
    """Body de POST /api/v1/ordenes-servicio. El estado, el idOrden y el idTecnico los pone el sistema."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "idCliente": "CLI-0001",
                "idMotocicleta": "MTO-0001",
                "motivoVisita": "Mantenimiento 5000 km y ruido en frenos",
                "fechaIngreso": "2026-10-14T08:30:00-05:00",
                "observaciones": "Cliente deja casco en recepción",
                "idCita": None,
            }
        },
    )

    id_cliente: str = Field(alias="idCliente")
    id_motocicleta: str = Field(alias="idMotocicleta")
    motivo_visita: str = Field(alias="motivoVisita", max_length=300)
    fecha_ingreso: datetime = Field(alias="fechaIngreso")
    observaciones: str | None = Field(default=None, max_length=500)
    id_cita: str | None = Field(default=None, alias="idCita")


class OrdenServicioRegistrada(BaseModel):
    """data de la respuesta de HU-016."""

    model_config = ConfigDict(from_attributes=True)

    id_orden: str = Field(serialization_alias="idOrden")
    id_cliente: str = Field(serialization_alias="idCliente")
    id_motocicleta: str = Field(serialization_alias="idMotocicleta")
    id_cita: str | None = Field(serialization_alias="idCita")
    motivo_visita: str = Field(serialization_alias="motivoVisita")
    estado: str
    fecha_ingreso: datetime = Field(serialization_alias="fechaIngreso")
    observaciones: str | None
    id_tecnico: str | None = Field(serialization_alias="idTecnico")

    @field_serializer("fecha_ingreso")
    def _fecha_iso(self, valor: datetime) -> str:
        return a_iso_bogota(valor)
