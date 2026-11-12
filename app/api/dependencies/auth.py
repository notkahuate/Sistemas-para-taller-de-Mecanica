"""Dependencias de seguridad: exigen token válido y rol permitido en cada endpoint."""
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decodificar_token
from app.domain.exceptions.errors import AccesoDenegadoError, NoAutorizadoError
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService

esquema_bearer = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UsuarioRepository(db))


def usuario_actual(credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer)) -> dict:
    """Devuelve {usuario, rol} del token. Sin token, token inválido o vencido: 401 AUTH-401."""
    if credenciales is None:
        raise NoAutorizadoError()
    try:
        datos = decodificar_token(credenciales.credentials)
    except jwt.PyJWTError:
        raise NoAutorizadoError() from None
    return {"usuario": datos.get("sub"), "rol": datos.get("rol")}


def requiere_rol(*roles: str):
    """Uso: dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))]."""

    def verificar(usuario: dict = Depends(usuario_actual)) -> dict:
        if usuario["rol"] not in roles:
            raise AccesoDenegadoError()
        return usuario

    return verificar
