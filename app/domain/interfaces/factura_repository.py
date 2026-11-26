"""Contrato del repositorio de facturas."""
from abc import ABC, abstractmethod


class IFacturaRepository(ABC):
    @abstractmethod
    def tiene_vigente(self, id_orden: str) -> bool:
        """True si la orden ya tiene una factura que no está anulada (una factura vigente por orden)."""
