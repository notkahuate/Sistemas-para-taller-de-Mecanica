"""Modelo de base de datos de repuestos consumidos en órdenes (tabla consumos_repuestos)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConsumoRepuestoModel(Base):
    __tablename__ = "consumos_repuestos"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_consumo: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    id_orden: Mapped[str] = mapped_column(String(12), ForeignKey("ordenes_servicio.id_orden"), index=True)
    id_actividad: Mapped[str] = mapped_column(String(12), ForeignKey("actividades_mantenimiento.id_actividad"))
    id_repuesto: Mapped[str] = mapped_column(String(12), ForeignKey("repuestos.id_repuesto"))
    referencia: Mapped[str] = mapped_column(String(30))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    id_movimiento: Mapped[str] = mapped_column(String(12), ForeignKey("movimientos_inventario.id_movimiento"))
    usuario: Mapped[str] = mapped_column(String(40))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
