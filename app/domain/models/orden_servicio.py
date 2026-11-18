"""Modelo de base de datos de órdenes de servicio (tabla ordenes_servicio)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OrdenServicioModel(Base):
    __tablename__ = "ordenes_servicio"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_orden: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    id_cliente: Mapped[str] = mapped_column(String(12), ForeignKey("clientes.id_cliente"), index=True)
    id_motocicleta: Mapped[str] = mapped_column(String(12), ForeignKey("motocicletas.id_motocicleta"), index=True)
    id_cita: Mapped[str | None] = mapped_column(String(12), nullable=True)
    motivo_visita: Mapped[str] = mapped_column(String(300))
    estado: Mapped[str] = mapped_column(String(15), default="recibida")
    fecha_ingreso: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observaciones: Mapped[str | None] = mapped_column(String(500), nullable=True)
    id_tecnico: Mapped[str | None] = mapped_column(String(12), nullable=True)
    # HU-017: datos de la asignación del técnico.
    id_especialidad_requerida: Mapped[str | None] = mapped_column(String(12), nullable=True)
    fecha_asignacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
