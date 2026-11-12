"""Entidad Cliente y reglas de formato del dominio (FUN-01)."""
import re
from dataclasses import dataclass
from datetime import datetime

TIPOS_DOCUMENTO = ("CC", "CE", "NIT", "PAS")
DOCUMENTO_RE = re.compile(r"^[A-Za-z0-9]{6,15}$")
TELEFONO_RE = re.compile(r"^[37]\d{9}$")
CORREO_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
ID_CLIENTE_RE = re.compile(r"^CLI-\d{4}$")

ESTADO_ACTIVO = "activo"


@dataclass
class Cliente:
    id_cliente: str
    tipo_documento: str
    numero_documento: str
    nombre_completo: str
    telefono: str
    correo: str
    direccion: str
    estado: str
    fecha_registro: datetime
    fecha_modificacion: datetime | None = None


def generar_id_cliente(secuencia: int) -> str:
    """El idCliente lo genera el sistema: prefijo CLI- y secuencia de 4 dígitos."""
    return f"CLI-{secuencia:04d}"
