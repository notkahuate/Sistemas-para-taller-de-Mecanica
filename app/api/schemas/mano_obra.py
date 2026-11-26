"""Esquemas de entrada y salida de HU-030 Registrar tiempo de mano de obra."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.responses import a_iso_bogota


class ManoObraRegistrar(BaseModel):
    """Body de PATCH /api/v1/actividades/{idActividad}/mano-obra."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={"example": {"horaInicio": "2026-11-20T09:15:00-05:00", "horaFin": "2026-11-20T10:00:00-05:00"}},
    )

    hora_inicio: datetime = Field(alias="horaInicio")
    hora_fin: datetime = Field(alias="horaFin")


class ManoObraRegistrada(BaseModel):
    """data de la respuesta de HU-030."""

    model_config = ConfigDict(from_attributes=True)

    id_actividad: str = Field(serialization_alias="idActividad")
    id_orden: str = Field(serialization_alias="idOrden")
    minutos: int
    tarifa_horaria: Decimal = Field(serialization_alias="tarifaHoraria")
    valor_mano_obra: Decimal = Field(serialization_alias="valorManoObra")
    hora_inicio: datetime = Field(serialization_alias="horaInicio")
    hora_fin: datetime = Field(serialization_alias="horaFin")

    @field_serializer("tarifa_horaria", "valor_mano_obra")
    def _dinero(self, valor: Decimal) -> float:
        return float(valor.quantize(Decimal("0.01")))

    @field_serializer("hora_inicio", "hora_fin")
    def _horas(self, valor: datetime) -> str:
        return a_iso_bogota(valor)
