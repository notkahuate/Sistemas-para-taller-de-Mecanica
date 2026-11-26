"""Modelo de base de datos de actividades de mantenimiento (tabla actividades_mantenimiento)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
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
    # HU-030: mano de obra calculada con la tarifa del técnico (alimenta HU-020/HU-061, RN-05).
    minutos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tarifa_horaria: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    valor_mano_obra: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
