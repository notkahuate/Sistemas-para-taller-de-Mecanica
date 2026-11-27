"""Contrato del repositorio de repuestos consumidos en órdenes."""
from abc import ABC, abstractmethod
from decimal import Decimal

from app.domain.entities.consumo_repuesto import ConsumoRepuesto


class IConsumoRepuestoRepository(ABC):
    @abstractmethod
    def registrar(self, consumo: dict, movimiento: dict) -> ConsumoRepuesto:
        """Guarda el consumo y su movimiento de salida en una sola transacción."""

    @abstractmethod
    def contar_por_orden(self, id_orden: str) -> int: ...

    @abstractmethod
    def total_repuestos(self, id_orden: str) -> Decimal:
        """Suma de cantidad * precioUnitario de los repuestos consumidos en la orden (HU-027)."""

    @abstractmethod
    def listar_por_orden(self, id_orden: str) -> list[ConsumoRepuesto]:
        """Repuestos consumidos en la orden en el orden en que se registraron."""
