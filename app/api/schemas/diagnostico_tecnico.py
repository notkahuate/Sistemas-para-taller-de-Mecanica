"""Esquemas de entrada y salida de HU-021 Registrar diagnóstico técnico."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.responses import a_iso_bogota


class DiagnosticoCrear(BaseModel):
    """Body de POST /api/v1/ordenes-servicio/{idOrden}/diagnosticos."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "hallazgos": "Pastillas de freno delantero al 20% de vida útil. Aceite oscuro a 5200 km.",
                "pruebas": "Prueba de frenado a 40 km/h; inspección visual de motor.",
                "diagnostico": "Desgaste de pastillas delanteras y aceite vencido por kilometraje.",
                "recomendaciones": "Cambio de pastillas y aceite 10W40. Revisar cadena en próximo servicio.",
            }
        },
    )

    hallazgos: str
    pruebas: str
    diagnostico: str
    recomendaciones: str | None = None


class DiagnosticoRegistrado(BaseModel):
    """data de la respuesta de HU-021."""

    model_config = ConfigDict(from_attributes=True)

    id_diagnostico: str = Field(serialization_alias="idDiagnostico")
    id_orden: str = Field(serialization_alias="idOrden")
    hallazgos: str
    pruebas: str
    diagnostico: str
    recomendaciones: str | None
    estado: str
    id_tecnico: str = Field(serialization_alias="idTecnico")
    fecha_registro: datetime = Field(serialization_alias="fechaRegistro")

    @field_serializer("fecha_registro")
    def _fecha(self, valor: datetime) -> str:
        return a_iso_bogota(valor)
