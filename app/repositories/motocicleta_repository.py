"""Repositorio de motocicletas: único lugar que lee y escribe la tabla motocicletas."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.motocicleta import Motocicleta, generar_id_motocicleta
from app.domain.interfaces.motocicleta_repository import IMotocicletaRepository
from app.domain.models.motocicleta import MotocicletaModel


def a_entidad(m: MotocicletaModel) -> Motocicleta:
    return Motocicleta(
        id_motocicleta=m.id_motocicleta or "",
        placa=m.placa,
        vin=m.vin,
        marca=m.marca,
        linea=m.linea,
        anio=m.anio,
        cilindraje=m.cilindraje,
        color=m.color,
        id_cliente=m.id_cliente,
        estado=m.estado,
    )


class MotocicletaRepository(IMotocicletaRepository):
    def __init__(self, db: Session):
        self.db = db

    def existe_placa(self, placa: str) -> bool:
        consulta = select(MotocicletaModel.secuencia).where(MotocicletaModel.placa == placa)
        return self.db.scalar(consulta) is not None

    def crear(self, datos: dict) -> Motocicleta:
        modelo = MotocicletaModel(**datos)
        self.db.add(modelo)
        try:
            self.db.flush()  # obtiene la secuencia para armar el idMotocicleta
            modelo.id_motocicleta = generar_id_motocicleta(modelo.secuencia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)

    def obtener_por_id(self, id_motocicleta: str) -> Motocicleta | None:
        modelo = self.db.scalar(select(MotocicletaModel).where(MotocicletaModel.id_motocicleta == id_motocicleta))
        return a_entidad(modelo) if modelo else None
