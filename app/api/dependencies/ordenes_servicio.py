"""Dependencias inyectables del módulo de órdenes de servicio."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.actividad_mantenimiento_repository import ActividadMantenimientoRepository
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.consumo_repuesto_repository import ConsumoRepuestoRepository
from app.repositories.diagnostico_tecnico_repository import DiagnosticoTecnicoRepository
from app.repositories.movimiento_inventario_repository import MovimientoInventarioRepository
from app.repositories.motocicleta_repository import MotocicletaRepository
from app.repositories.orden_servicio_repository import OrdenServicioRepository
from app.repositories.repuesto_repository import RepuestoRepository
from app.repositories.tecnico_repository import TecnicoRepository
from app.services.actividad_mantenimiento_service import ActividadMantenimientoService
from app.services.consumo_repuesto_service import ConsumoRepuestoService
from app.services.diagnostico_tecnico_service import DiagnosticoTecnicoService
from app.services.orden_servicio_service import OrdenServicioService


def get_orden_servicio_service(db: Session = Depends(get_db)) -> OrdenServicioService:
    return OrdenServicioService(
        OrdenServicioRepository(db),
        ClienteRepository(db),
        MotocicletaRepository(db),
        TecnicoRepository(db),
        ActividadMantenimientoRepository(db),
        DiagnosticoTecnicoRepository(db),
        ConsumoRepuestoRepository(db),
    )


def get_actividad_service(db: Session = Depends(get_db)) -> ActividadMantenimientoService:
    return ActividadMantenimientoService(ActividadMantenimientoRepository(db), OrdenServicioRepository(db))


def get_diagnostico_service(db: Session = Depends(get_db)) -> DiagnosticoTecnicoService:
    return DiagnosticoTecnicoService(DiagnosticoTecnicoRepository(db), OrdenServicioRepository(db))


def get_consumo_service(db: Session = Depends(get_db)) -> ConsumoRepuestoService:
    return ConsumoRepuestoService(
        ConsumoRepuestoRepository(db),
        OrdenServicioRepository(db),
        ActividadMantenimientoRepository(db),
        RepuestoRepository(db),
        MovimientoInventarioRepository(db),
    )
