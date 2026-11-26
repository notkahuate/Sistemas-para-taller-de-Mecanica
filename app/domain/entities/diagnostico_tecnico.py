"""Entidad Diagnóstico técnico de una orden de servicio (FUN-21)."""
from dataclasses import dataclass
from datetime import datetime

ESTADO_REGISTRADO = "registrado"
TEXTO_MIN, TEXTO_MAX = 15, 1000  # hallazgos, pruebas y diagnostico: mínimo 15 caracteres


@dataclass
class DiagnosticoTecnico:
    id_diagnostico: str
    id_orden: str
    hallazgos: str
    pruebas: str
    diagnostico: str
    recomendaciones: str | None
    estado: str
    id_tecnico: str
    fecha_registro: datetime


def generar_id_diagnostico(secuencia: int) -> str:
    """El idDiagnostico lo genera el sistema: prefijo DG- y secuencia de 4 dígitos."""
    return f"DG-{secuencia:04d}"
