"""Contratos JSON de motocicletas (camelCase, como en el Parcial #2)."""
from pydantic import BaseModel, ConfigDict, Field


class MotocicletaCrear(BaseModel):
    """Body de POST /api/v1/motocicletas. El estado y el idMotocicleta los pone el sistema."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "placa": "ABC12D",
                "vin": "9BWZZZZ377VT00432",
                "marca": "Yamaha",
                "linea": "FZ 2.0",
                "anio": 2023,
                "cilindraje": 150,
                "color": "Azul",
                "idCliente": "CLI-0001",
            }
        },
    )

    placa: str = Field(max_length=10)
    vin: str | None = Field(default=None, max_length=20)
    marca: str = Field(max_length=60)
    linea: str = Field(max_length=60)
    anio: int
    cilindraje: int
    color: str = Field(max_length=30)
    id_cliente: str = Field(alias="idCliente")


class MotocicletaRegistrada(BaseModel):
    """data de la respuesta de HU-006."""

    model_config = ConfigDict(from_attributes=True)

    id_motocicleta: str = Field(serialization_alias="idMotocicleta")
    placa: str
    vin: str | None
    marca: str
    linea: str
    anio: int
    cilindraje: int
    color: str
    id_cliente: str = Field(serialization_alias="idCliente")
    estado: str


class MotocicletaDetalle(BaseModel):
    """data de la respuesta de HU-007: la motocicleta con el nombre de su propietario."""

    id_motocicleta: str = Field(serialization_alias="idMotocicleta")
    placa: str
    vin: str | None
    marca: str
    linea: str
    anio: int
    cilindraje: int
    color: str
    id_cliente: str = Field(serialization_alias="idCliente")
    nombre_propietario: str | None = Field(serialization_alias="nombrePropietario")
    estado: str
