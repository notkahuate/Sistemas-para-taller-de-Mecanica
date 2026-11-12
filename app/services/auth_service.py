"""Casos de uso de autenticación (HT-02)."""
from app.core.config import settings
from app.core.security import crear_token, hash_clave, verificar_clave
from app.domain.entities.usuario import (
    ROL_ADMINISTRADOR,
    ROL_INVENTARIO,
    ROL_RECEPCION,
    ROL_TECNICO,
    Usuario,
)
from app.domain.exceptions.errors import AppError
from app.repositories.usuario_repository import UsuarioRepository

# Usuarios de demostración que se crean si la tabla está vacía.
# Cambien estas claves antes de cualquier despliegue real.
USUARIOS_INICIALES = (
    ("admin", "Administrador del taller", ROL_ADMINISTRADOR, "Admin123*"),
    ("recepcion", "Auxiliar de recepción", ROL_RECEPCION, "Recepcion123*"),
    ("tecnico", "Técnico del taller", ROL_TECNICO, "Tecnico123*"),
    ("inventario", "Encargado de inventario", ROL_INVENTARIO, "Inventario123*"),
)


class CredencialesInvalidasError(AppError):
    status_code = 401

    def __init__(self):
        super().__init__(
            "No fue posible iniciar sesión.", "AUTH-CREDENCIALES", "Usuario o clave incorrectos.", "credenciales"
        )


class AuthService:
    def __init__(self, repositorio: UsuarioRepository):
        self.repositorio = repositorio

    def iniciar_sesion(self, usuario: str, clave: str) -> dict:
        encontrado = self.repositorio.obtener_por_usuario(usuario)
        if encontrado is None or not encontrado.activo or not verificar_clave(clave, encontrado.hash_clave):
            raise CredencialesInvalidasError()
        return {
            "accessToken": crear_token(encontrado.usuario, encontrado.rol),
            "tokenType": "bearer",
            "expiraEnSegundos": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "usuario": encontrado.usuario,
            "rol": encontrado.rol,
        }

    def crear_usuarios_iniciales(self) -> None:
        if self.repositorio.contar() > 0:
            return
        for usuario, nombre, rol, clave in USUARIOS_INICIALES:
            self.repositorio.crear(Usuario(usuario=usuario, nombre=nombre, rol=rol, hash_clave=hash_clave(clave)))
