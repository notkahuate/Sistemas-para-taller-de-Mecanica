"""Entidad Motocicleta y reglas de formato del dominio (FUN-06)."""
import re
from dataclasses import dataclass
from datetime import date

PLACA_RE = re.compile(r"^[A-Z0-9]{5,6}$")
VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
ANIO_MINIMO = 1980
CILINDRAJE_MINIMO = 50
CILINDRAJE_MAXIMO = 1300
ESTADO_ACTIVA = "activa"


def anio_maximo() -> int:
    """El año del modelo puede ser hasta el año actual + 1."""
    return date.today().year + 1


@dataclass
class Motocicleta:
    id_motocicleta: str
    placa: str
    vin: str | None
    marca: str
    linea: str
    anio: int
    cilindraje: int
    color: str
    id_cliente: str
    estado: str


def generar_id_motocicleta(secuencia: int) -> str:
    """El idMotocicleta lo genera el sistema: prefijo MTO- y secuencia de 4 dígitos."""
    return f"MTO-{secuencia:04d}"
