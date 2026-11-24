"""Esquemas de entrada y salida de HU-026 Registrar actividades de mantenimiento."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.responses import a_iso_bogota


class ActividadCrear(BaseModel):
    """Body de POST /api/v1/ordenes-servicio/{idOrden}/actividades."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "nombre": "Cambio de pastillas de freno delanteras",
                "estado": "en_ejecucion",
                "observaciones": "Se utiliza kit original Yamaha",
                "horaInicio": "2026-11-20T09:15:00-05:00",
            }
        },
    )

    nombre: str
    estado: str
    observaciones: str | None = Field(default=None, max_length=500)
    hora_inicio: datetime = Field(alias="horaInicio")


class ActividadRegistrada(BaseModel):
    """data de la respuesta de HU-026."""

    model_config = ConfigDict(from_attributes=True)

    id_actividad: str = Field(serialization_alias="idActividad")
    id_orden: str = Field(serialization_alias="idOrden")
    id_tecnico: str = Field(serialization_alias="idTecnico")
    nombre: str
    estado: str
    hora_inicio: datetime = Field(serialization_alias="horaInicio")
    hora_fin: datetime | None = Field(serialization_alias="horaFin")

    @field_serializer("hora_inicio")
    def _hora_inicio(self, valor: datetime) -> str:
        return a_iso_bogota(valor)

    @field_serializer("hora_fin")
    def _hora_fin(self, valor: datetime | None) -> str | None:
        return a_iso_bogota(valor) if valor else None
