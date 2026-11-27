"""Contrato del repositorio de pagos de clientes."""
from abc import ABC, abstractmethod
from decimal import Decimal

from app.domain.entities.factura import Factura
from app.domain.entities.pago_cliente import PagoCliente


class IPagoClienteRepository(ABC):
    @abstractmethod
    def registrar(self, pago: dict, saldo_pendiente: Decimal, estado_factura: str) -> tuple[PagoCliente, Factura]:
        """Guarda el pago y actualiza saldo y estado de la factura en una sola transacción (RN-11)."""
