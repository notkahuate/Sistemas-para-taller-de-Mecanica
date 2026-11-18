"""Contrato que debe cumplir cualquier repositorio de órdenes de servicio."""
from abc import ABC, abstractmethod

from app.domain.entities.orden_servicio import OrdenServicio


class IOrdenServicioRepository(ABC):
    @abstractmethod
    def tiene_orden_abierta(self, id_motocicleta: str) -> bool: ...

    @abstractmethod
    def crear(self, datos: dict) -> OrdenServicio: ...
