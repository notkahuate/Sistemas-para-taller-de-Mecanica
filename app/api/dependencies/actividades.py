"""Dependencias del módulo de actividades de mantenimiento."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.actividad_mantenimiento_repository import ActividadMantenimientoRepository
from app.repositories.orden_servicio_repository import OrdenServicioRepository
from app.repositories.tecnico_repository import TecnicoRepository
from app.services.mano_obra_service import ManoObraService


def get_mano_obra_service(db: Session = Depends(get_db)) -> ManoObraService:
    return ManoObraService(ActividadMantenimientoRepository(db), OrdenServicioRepository(db), TecnicoRepository(db))
