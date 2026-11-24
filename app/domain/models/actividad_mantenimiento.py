"""Modelo de base de datos de actividades de mantenimiento (tabla actividades_mantenimiento)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ActividadMantenimientoModel(Base):
    __tablename__ = "actividades_mantenimiento"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_actividad: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    id_orden: Mapped[str] = mapped_column(String(12), ForeignKey("ordenes_servicio.id_orden"), index=True)
    id_tecnico: Mapped[str] = mapped_column(String(12))
    nombre: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(15))
    observaciones: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    hora_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
