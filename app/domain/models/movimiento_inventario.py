"""Modelo de base de datos de movimientos de inventario (tabla movimientos_inventario)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MovimientoInventarioModel(Base):
    __tablename__ = "movimientos_inventario"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_movimiento: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    id_repuesto: Mapped[str] = mapped_column(String(12), ForeignKey("repuestos.id_repuesto"), index=True)
    referencia: Mapped[str] = mapped_column(String(30))
    tipo: Mapped[str] = mapped_column(String(10))
    motivo: Mapped[str] = mapped_column(String(30))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    stock_resultante: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    id_recepcion: Mapped[str | None] = mapped_column(String(12), nullable=True)
    ubicacion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    usuario: Mapped[str] = mapped_column(String(40))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
