"""Contrato que debe cumplir cualquier repositorio de motocicletas."""
from abc import ABC, abstractmethod

from app.domain.entities.motocicleta import Motocicleta


class IMotocicletaRepository(ABC):
    @abstractmethod
    def existe_placa(self, placa: str) -> bool: ...

    @abstractmethod
    def crear(self, datos: dict) -> Motocicleta: ...
