"""Repositorio de repuestos: único lugar que lee y escribe la tabla repuestos."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.repuesto import Repuesto, generar_id_repuesto
from app.domain.interfaces.repuesto_repository import IRepuestoRepository
from app.domain.models.repuesto import RepuestoModel


def a_entidad(m: RepuestoModel) -> Repuesto:
    return Repuesto(
        id_repuesto=m.id_repuesto or "",
        referencia=m.referencia,
        nombre=m.nombre,
        descripcion=m.descripcion,
        id_categoria=m.id_categoria,
        id_proveedor=m.id_proveedor,
        costo=m.costo,
        precio=m.precio,
        stock_minimo=m.stock_minimo,
        estado=m.estado,
    )


class RepuestoRepository(IRepuestoRepository):
    def __init__(self, db: Session):
        self.db = db

    def existe_referencia(self, referencia: str) -> bool:
        # La referencia es única sin importar mayúsculas o minúsculas.
        consulta = select(RepuestoModel.secuencia).where(func.upper(RepuestoModel.referencia) == referencia.upper())
        return self.db.scalar(consulta) is not None

    def crear(self, datos: dict) -> Repuesto:
        modelo = RepuestoModel(**datos)
        self.db.add(modelo)
        try:
            self.db.flush()  # obtiene la secuencia para armar el idRepuesto
            modelo.id_repuesto = generar_id_repuesto(modelo.secuencia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)
