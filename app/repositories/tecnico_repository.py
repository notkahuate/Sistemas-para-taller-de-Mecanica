"""Repositorio de técnicos: único lugar que lee y escribe la tabla tecnicos."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.tecnico import Tecnico, generar_id_tecnico
from app.domain.interfaces.tecnico_repository import ITecnicoRepository
from app.domain.models.tecnico import TecnicoModel


def a_entidad(m: TecnicoModel) -> Tecnico:
    return Tecnico(
        id_tecnico=m.id_tecnico or "",
        tipo_documento=m.tipo_documento,
        numero_documento=m.numero_documento,
        nombre_completo=m.nombre_completo,
        telefono=m.telefono,
        correo=m.correo,
        cargo=m.cargo,
        fecha_ingreso=m.fecha_ingreso,
        tarifa_horaria=m.tarifa_horaria,
        estado=m.estado,
    )


class TecnicoRepository(ITecnicoRepository):
    def __init__(self, db: Session):
        self.db = db

    def existe_documento(self, numero_documento: str) -> bool:
        consulta = select(TecnicoModel.secuencia).where(TecnicoModel.numero_documento == numero_documento)
        return self.db.scalar(consulta) is not None

    def crear(self, datos: dict) -> Tecnico:
        modelo = TecnicoModel(**datos)
        self.db.add(modelo)
        try:
            self.db.flush()  # obtiene la secuencia para armar el idTecnico
            modelo.id_tecnico = generar_id_tecnico(modelo.secuencia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)

    def obtener_por_id(self, id_tecnico: str) -> Tecnico | None:
        modelo = self.db.scalar(select(TecnicoModel).where(TecnicoModel.id_tecnico == id_tecnico))
        return a_entidad(modelo) if modelo else None
