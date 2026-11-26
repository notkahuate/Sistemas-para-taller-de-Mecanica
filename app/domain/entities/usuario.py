"""Entidad Usuario y roles del sistema (HT-02)."""
from dataclasses import dataclass

ROL_ADMINISTRADOR = "administrador"
ROL_RECEPCION = "recepcion"
ROL_TECNICO = "tecnico"
ROL_INVENTARIO = "inventario"
ROLES = (ROL_ADMINISTRADOR, ROL_RECEPCION, ROL_TECNICO, ROL_INVENTARIO)


@dataclass
class Usuario:
    usuario: str
    nombre: str
    rol: str
    hash_clave: str
    activo: bool = True
