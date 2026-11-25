"""Contrato del repositorio de diagnósticos técnicos."""
from abc import ABC, abstractmethod

from app.domain.entities.diagnostico_tecnico import DiagnosticoTecnico


class IDiagnosticoTecnicoRepository(ABC):
    @abstractmethod
    def tiene_vigente(self, id_orden: str) -> bool: ...

    @abstractmethod
    def crear(self, datos: dict) -> DiagnosticoTecnico: ...
