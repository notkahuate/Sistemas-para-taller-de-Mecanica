"""Repositorio de diagnósticos técnicos: único lugar que lee y escribe la tabla diagnosticos_tecnicos."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.diagnostico_tecnico import ESTADO_REGISTRADO, DiagnosticoTecnico, generar_id_diagnostico
from app.domain.interfaces.diagnostico_tecnico_repository import IDiagnosticoTecnicoRepository
from app.domain.models.diagnostico_tecnico import DiagnosticoTecnicoModel


def a_entidad(m: DiagnosticoTecnicoModel) -> DiagnosticoTecnico:
    return DiagnosticoTecnico(
        id_diagnostico=m.id_diagnostico or "",
        id_orden=m.id_orden,
        hallazgos=m.hallazgos,
        pruebas=m.pruebas,
        diagnostico=m.diagnostico,
        recomendaciones=m.recomendaciones,
        estado=m.estado,
        id_tecnico=m.id_tecnico,
        fecha_registro=m.fecha_registro,
    )


class DiagnosticoTecnicoRepository(IDiagnosticoTecnicoRepository):
    def __init__(self, db: Session):
        self.db = db

    def tiene_vigente(self, id_orden: str) -> bool:
        consulta = select(DiagnosticoTecnicoModel.secuencia).where(
            DiagnosticoTecnicoModel.id_orden == id_orden,
            DiagnosticoTecnicoModel.estado == ESTADO_REGISTRADO,
        )
        return self.db.scalar(consulta) is not None

    def crear(self, datos: dict) -> DiagnosticoTecnico:
        modelo = DiagnosticoTecnicoModel(**datos)
        self.db.add(modelo)
        try:
            self.db.flush()  # obtiene la secuencia para armar el idDiagnostico
            modelo.id_diagnostico = generar_id_diagnostico(modelo.secuencia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)
