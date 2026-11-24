"""Contrato del repositorio de actividades de mantenimiento."""
from abc import ABC, abstractmethod

from app.domain.entities.actividad_mantenimiento import ActividadMantenimiento


class IActividadMantenimientoRepository(ABC):
    @abstractmethod
    def crear(self, datos: dict) -> ActividadMantenimiento: ...
