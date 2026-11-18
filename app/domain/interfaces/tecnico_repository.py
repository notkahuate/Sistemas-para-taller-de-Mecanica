"""Contrato que debe cumplir cualquier repositorio de técnicos."""
from abc import ABC, abstractmethod

from app.domain.entities.tecnico import Tecnico


class ITecnicoRepository(ABC):
    @abstractmethod
    def existe_documento(self, numero_documento: str) -> bool: ...

    @abstractmethod
    def crear(self, datos: dict) -> Tecnico: ...

    @abstractmethod
    def obtener_por_id(self, id_tecnico: str) -> Tecnico | None: ...
