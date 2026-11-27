"""Repositorio de actividades de mantenimiento: único lugar que lee y escribe la tabla actividades_mantenimiento."""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.actividad_mantenimiento import ESTADO_COMPLETADA, ActividadMantenimiento, generar_id_actividad
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
        minutos=m.minutos,
        tarifa_horaria=m.tarifa_horaria,
        valor_mano_obra=m.valor_mano_obra,
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

    def contar_por_orden(self, id_orden: str) -> int:
        consulta = select(func.count()).where(ActividadMantenimientoModel.id_orden == id_orden)
        return self.db.scalar(consulta) or 0

    def obtener_por_id(self, id_actividad: str) -> ActividadMantenimiento | None:
        modelo = self.db.scalar(
            select(ActividadMantenimientoModel).where(ActividadMantenimientoModel.id_actividad == id_actividad)
        )
        return a_entidad(modelo) if modelo else None

    def registrar_mano_obra(self, id_actividad: str, datos: dict) -> ActividadMantenimiento:
        """Guarda horaInicio, horaFin, minutos, tarifa y valor de mano de obra de la actividad."""
        modelo = self.db.scalar(
            select(ActividadMantenimientoModel).where(ActividadMantenimientoModel.id_actividad == id_actividad)
        )
        try:
            for campo, valor in datos.items():
                setattr(modelo, campo, valor)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)

    def contar_completadas(self, id_orden: str) -> int:
        consulta = select(func.count()).where(
            ActividadMantenimientoModel.id_orden == id_orden,
            ActividadMantenimientoModel.estado == ESTADO_COMPLETADA,
        )
        return self.db.scalar(consulta) or 0

    def total_mano_obra(self, id_orden: str) -> Decimal:
        filas = self.db.execute(
            select(ActividadMantenimientoModel.minutos, ActividadMantenimientoModel.tarifa_horaria).where(
                ActividadMantenimientoModel.id_orden == id_orden,
                ActividadMantenimientoModel.minutos.is_not(None),
            )
        ).all()
        return sum((Decimal(m) * Decimal(t) / Decimal(60) for m, t in filas), Decimal("0"))

    def listar_por_orden(self, id_orden: str) -> list[ActividadMantenimiento]:
        consulta = (
            select(ActividadMantenimientoModel)
            .where(ActividadMantenimientoModel.id_orden == id_orden)
            .order_by(ActividadMantenimientoModel.secuencia)
        )
        return [a_entidad(m) for m in self.db.scalars(consulta)]
