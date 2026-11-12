"""Endpoint de inicio de sesión (HT-02)."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_auth_service
from app.api.schemas.auth import LoginRequest
from app.core.responses import envelope
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post(
    "/login",
    summary="HT-02 Iniciar sesión",
    description="Devuelve un token JWT. Úsalo en el botón Authorize de Swagger o en el encabezado Authorization: Bearer <token>.",
)
def iniciar_sesion(body: LoginRequest, servicio: AuthService = Depends(get_auth_service)):
    data = servicio.iniciar_sesion(body.usuario, body.clave)
    return envelope(success=True, message="Inicio de sesión exitoso", data=data)
