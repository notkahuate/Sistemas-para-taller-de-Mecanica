"""Repositorio de usuarios: único lugar que lee y escribe la tabla usuarios."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.usuario import Usuario
from app.domain.models.usuario import UsuarioModel


def a_entidad(m: UsuarioModel) -> Usuario:
    return Usuario(usuario=m.usuario, nombre=m.nombre, rol=m.rol, hash_clave=m.hash_clave, activo=m.activo)


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_usuario(self, usuario: str) -> Usuario | None:
        modelo = self.db.scalar(select(UsuarioModel).where(UsuarioModel.usuario == usuario))
        return a_entidad(modelo) if modelo else None

    def contar(self) -> int:
        return self.db.scalar(select(func.count(UsuarioModel.id))) or 0

    def crear(self, usuario: Usuario) -> None:
        self.db.add(
            UsuarioModel(
                usuario=usuario.usuario,
                nombre=usuario.nombre,
                rol=usuario.rol,
                hash_clave=usuario.hash_clave,
                activo=usuario.activo,
            )
        )
        self.db.commit()
