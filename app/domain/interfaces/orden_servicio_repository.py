"""Contrato que debe cumplir cualquier repositorio de órdenes de servicio."""
from abc import ABC, abstractmethod

from app.domain.entities.orden_servicio import OrdenServicio


class IOrdenServicioRepository(ABC):
    @abstractmethod
    def tiene_orden_abierta(self, id_motocicleta: str) -> bool: ...

    @abstractmethod
    def crear(self, datos: dict) -> OrdenServicio: ...

    @abstractmethod
    def obtener_por_id(self, id_orden: str) -> OrdenServicio | None: ...

    @abstractmethod
    def asignar_tecnico(self, id_orden: str, datos: dict) -> OrdenServicio: ...

    @abstractmethod
    def cerrar_y_facturar(self, id_orden: str, fecha_cierre, factura: dict):
        """Pasa la orden a finalizada y crea su factura en la misma transacción (RN-05). Devuelve (orden, factura)."""
