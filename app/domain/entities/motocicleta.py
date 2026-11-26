"""Entidad Motocicleta y reglas de formato del dominio (FUN-06)."""
import re
from dataclasses import dataclass
from datetime import date

PLACA_RE = re.compile(r"^[A-Z0-9]{5,6}$")
PLACA_CARACTERES_RE = re.compile(r"^[A-Z0-9]*$")
ID_MOTOCICLETA_RE = re.compile(r"^MTO-\d{4}$")
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


def normalizar_placa(placa: str) -> str:
    """RN-12: la placa es única sin importar mayúsculas o espacios, así que se compara normalizada."""
    return placa.strip().upper()


def validar_placa_consulta(placa: str) -> str | None:
    """Devuelve el detalle del error si la placa (ya normalizada) no sirve para consultar, o None si es válida."""
    if not placa:
        return "La placa es obligatoria."
    if not PLACA_CARACTERES_RE.match(placa):
        return "Placa con caracteres especiales"
    if not PLACA_RE.match(placa):
        return "Placa con formato inválido"
    return None
