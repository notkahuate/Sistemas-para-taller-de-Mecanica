"""Dependencias inyectables del módulo de órdenes de servicio."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.actividad_mantenimiento_repository import ActividadMantenimientoRepository
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.motocicleta_repository import MotocicletaRepository
from app.repositories.orden_servicio_repository import OrdenServicioRepository
from app.repositories.tecnico_repository import TecnicoRepository
from app.services.actividad_mantenimiento_service import ActividadMantenimientoService
from app.services.orden_servicio_service import OrdenServicioService


def get_orden_servicio_service(db: Session = Depends(get_db)) -> OrdenServicioService:
    return OrdenServicioService(
        OrdenServicioRepository(db),
        ClienteRepository(db),
        MotocicletaRepository(db),
        TecnicoRepository(db),
        ActividadMantenimientoRepository(db),
    )


def get_actividad_service(db: Session = Depends(get_db)) -> ActividadMantenimientoService:
    return ActividadMantenimientoService(ActividadMantenimientoRepository(db), OrdenServicioRepository(db))
