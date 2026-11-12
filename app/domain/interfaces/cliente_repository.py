"""Contrato que debe cumplir cualquier repositorio de clientes."""
from abc import ABC, abstractmethod

from app.domain.entities.cliente import Cliente


class IClienteRepository(ABC):
    @abstractmethod
    def existe_documento(self, numero_documento: str) -> bool: ...

    @abstractmethod
    def crear(self, datos: dict) -> Cliente: ...
