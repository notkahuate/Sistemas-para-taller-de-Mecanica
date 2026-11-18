"""Contrato que debe cumplir cualquier repositorio de repuestos."""
from abc import ABC, abstractmethod

from app.domain.entities.repuesto import Repuesto


class IRepuestoRepository(ABC):
    @abstractmethod
    def existe_referencia(self, referencia: str) -> bool: ...

    @abstractmethod
    def crear(self, datos: dict) -> Repuesto: ...

    @abstractmethod
    def obtener_por_referencia(self, referencia: str) -> Repuesto | None: ...
