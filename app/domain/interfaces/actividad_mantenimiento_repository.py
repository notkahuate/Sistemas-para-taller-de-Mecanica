"""Contrato del repositorio de actividades de mantenimiento."""
from abc import ABC, abstractmethod

from app.domain.entities.actividad_mantenimiento import ActividadMantenimiento


class IActividadMantenimientoRepository(ABC):
    @abstractmethod
    def crear(self, datos: dict) -> ActividadMantenimiento: ...

    @abstractmethod
    def contar_por_orden(self, id_orden: str) -> int: ...
