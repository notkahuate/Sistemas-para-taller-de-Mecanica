"""Dependencias inyectables del módulo de órdenes de servicio."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.motocicleta_repository import MotocicletaRepository
from app.repositories.orden_servicio_repository import OrdenServicioRepository
from app.repositories.tecnico_repository import TecnicoRepository
from app.services.orden_servicio_service import OrdenServicioService


def get_orden_servicio_service(db: Session = Depends(get_db)) -> OrdenServicioService:
    return OrdenServicioService(
        OrdenServicioRepository(db), ClienteRepository(db), MotocicletaRepository(db), TecnicoRepository(db)
    )
