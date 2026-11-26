"""Contrato del repositorio de actividades de mantenimiento."""
from abc import ABC, abstractmethod

from app.domain.entities.actividad_mantenimiento import ActividadMantenimiento


class IActividadMantenimientoRepository(ABC):
    @abstractmethod
    def crear(self, datos: dict) -> ActividadMantenimiento: ...

    @abstractmethod
    def obtener_por_id(self, id_actividad: str) -> ActividadMantenimiento | None: ...

    @abstractmethod
    def registrar_mano_obra(self, id_actividad: str, datos: dict) -> ActividadMantenimiento: ...

    @abstractmethod
    def contar_por_orden(self, id_orden: str) -> int: ...
