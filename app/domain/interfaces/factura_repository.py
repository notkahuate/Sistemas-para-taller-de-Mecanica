"""Contrato del repositorio de facturas."""
from abc import ABC, abstractmethod

from app.domain.entities.factura import Factura


class IFacturaRepository(ABC):
    @abstractmethod
    def tiene_vigente(self, id_orden: str) -> bool:
        """True si la orden ya tiene una factura que no está anulada (una factura vigente por orden)."""

    @abstractmethod
    def crear(self, datos: dict) -> Factura:
        """Persiste la factura y le asigna su idFactura (FAC-NNNN)."""

    @abstractmethod
    def obtener_por_id(self, id_factura: str) -> Factura | None: ...
