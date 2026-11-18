"""Entidad Técnico (FUN-76)."""
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

ESTADO_ACTIVO = "activo"
ID_TECNICO_RE = re.compile(r"^TEC-\d{4}$")


@dataclass
class Tecnico:
    id_tecnico: str
    tipo_documento: str
    numero_documento: str
    nombre_completo: str
    telefono: str
    correo: str
    cargo: str
    fecha_ingreso: date
    tarifa_horaria: Decimal
    estado: str


def generar_id_tecnico(secuencia: int) -> str:
    """El idTecnico lo genera el sistema: prefijo TEC- y secuencia de 4 dígitos."""
    return f"TEC-{secuencia:04d}"
