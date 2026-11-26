"""Contrato del repositorio de repuestos consumidos en órdenes."""
from abc import ABC, abstractmethod

from app.domain.entities.consumo_repuesto import ConsumoRepuesto


class IConsumoRepuestoRepository(ABC):
    @abstractmethod
    def registrar(self, consumo: dict, movimiento: dict) -> ConsumoRepuesto:
        """Guarda el consumo y su movimiento de salida en una sola transacción."""

    @abstractmethod
    def contar_por_orden(self, id_orden: str) -> int: ...
