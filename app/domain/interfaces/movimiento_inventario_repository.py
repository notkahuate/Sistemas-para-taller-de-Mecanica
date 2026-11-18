"""Contrato que debe cumplir cualquier repositorio de movimientos de inventario."""
from abc import ABC, abstractmethod
from decimal import Decimal

from app.domain.entities.movimiento_inventario import MovimientoInventario


class IMovimientoInventarioRepository(ABC):
    @abstractmethod
    def stock_actual(self, id_repuesto: str) -> Decimal: ...

    @abstractmethod
    def registrar(self, datos: dict) -> MovimientoInventario: ...
