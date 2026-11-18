"""Dependencias inyectables del módulo de inventario."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.movimiento_inventario_repository import MovimientoInventarioRepository
from app.repositories.repuesto_repository import RepuestoRepository
from app.services.inventario_service import InventarioService


def get_inventario_service(db: Session = Depends(get_db)) -> InventarioService:
    return InventarioService(MovimientoInventarioRepository(db), RepuestoRepository(db))
