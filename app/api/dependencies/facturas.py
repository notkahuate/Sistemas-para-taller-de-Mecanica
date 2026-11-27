"""Dependencias del módulo de facturación."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.actividad_mantenimiento_repository import ActividadMantenimientoRepository
from app.repositories.consumo_repuesto_repository import ConsumoRepuestoRepository
from app.repositories.factura_repository import FacturaRepository
from app.repositories.orden_servicio_repository import OrdenServicioRepository
from app.services.factura_service import FacturaService


def get_factura_service(db: Session = Depends(get_db)) -> FacturaService:
    return FacturaService(
        OrdenServicioRepository(db),
        ActividadMantenimientoRepository(db),
        ConsumoRepuestoRepository(db),
        FacturaRepository(db),
    )
