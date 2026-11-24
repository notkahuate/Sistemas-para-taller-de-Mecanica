"""Repositorio de actividades de mantenimiento: único lugar que lee y escribe la tabla actividades_mantenimiento."""
from sqlalchemy.orm import Session

from app.domain.entities.actividad_mantenimiento import ActividadMantenimiento, generar_id_actividad
from app.domain.interfaces.actividad_mantenimiento_repository import IActividadMantenimientoRepository
from app.domain.models.actividad_mantenimiento import ActividadMantenimientoModel


def a_entidad(m: ActividadMantenimientoModel) -> ActividadMantenimiento:
    return ActividadMantenimiento(
        id_actividad=m.id_actividad or "",
        id_orden=m.id_orden,
        id_tecnico=m.id_tecnico,
        nombre=m.nombre,
        estado=m.estado,
        observaciones=m.observaciones,
        hora_inicio=m.hora_inicio,
        hora_fin=m.hora_fin,
    )


class ActividadMantenimientoRepository(IActividadMantenimientoRepository):
    def __init__(self, db: Session):
        self.db = db

    def crear(self, datos: dict) -> ActividadMantenimiento:
        modelo = ActividadMantenimientoModel(**datos)
        self.db.add(modelo)
        try:
            self.db.flush()  # obtiene la secuencia para armar el idActividad
            modelo.id_actividad = generar_id_actividad(modelo.secuencia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)
