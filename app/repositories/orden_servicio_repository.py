"""Repositorio de órdenes de servicio: único lugar que lee y escribe la tabla ordenes_servicio."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.orden_servicio import ESTADOS_ABIERTOS, OrdenServicio, generar_id_orden
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository
from app.domain.models.orden_servicio import OrdenServicioModel


def a_entidad(m: OrdenServicioModel) -> OrdenServicio:
    return OrdenServicio(
        id_orden=m.id_orden or "",
        id_cliente=m.id_cliente,
        id_motocicleta=m.id_motocicleta,
        id_cita=m.id_cita,
        motivo_visita=m.motivo_visita,
        estado=m.estado,
        fecha_ingreso=m.fecha_ingreso,
        observaciones=m.observaciones,
        id_tecnico=m.id_tecnico,
        id_especialidad_requerida=m.id_especialidad_requerida,
        fecha_asignacion=m.fecha_asignacion,
        fecha_cierre=m.fecha_cierre,
    )


class OrdenServicioRepository(IOrdenServicioRepository):
    def __init__(self, db: Session):
        self.db = db

    def tiene_orden_abierta(self, id_motocicleta: str) -> bool:
        consulta = select(OrdenServicioModel.secuencia).where(
            OrdenServicioModel.id_motocicleta == id_motocicleta,
            OrdenServicioModel.estado.in_(ESTADOS_ABIERTOS),
        )
        return self.db.scalar(consulta) is not None

    def crear(self, datos: dict) -> OrdenServicio:
        modelo = OrdenServicioModel(**datos)
        self.db.add(modelo)
        try:
            self.db.flush()  # obtiene la secuencia para armar el idOrden
            modelo.id_orden = generar_id_orden(modelo.secuencia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)

    def obtener_por_id(self, id_orden: str) -> OrdenServicio | None:
        modelo = self.db.scalar(select(OrdenServicioModel).where(OrdenServicioModel.id_orden == id_orden))
        return a_entidad(modelo) if modelo else None

    def asignar_tecnico(self, id_orden: str, datos: dict) -> OrdenServicio:
        """Guarda idTecnico, idEspecialidadRequerida, fechaAsignacion y el nuevo estado de la orden."""
        modelo = self.db.scalar(select(OrdenServicioModel).where(OrdenServicioModel.id_orden == id_orden))
        try:
            for campo, valor in datos.items():
                setattr(modelo, campo, valor)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)
