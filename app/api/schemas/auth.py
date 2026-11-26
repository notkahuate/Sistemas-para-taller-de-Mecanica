"""Contratos JSON de autenticación (HT-02)."""
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"usuario": "recepcion", "clave": "Recepcion123*"}},
    )

    usuario: str = Field(min_length=1, max_length=40)
    clave: str = Field(min_length=1, max_length=100)
