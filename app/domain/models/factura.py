"""Modelo de base de datos de facturas de servicio (tabla facturas)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FacturaModel(Base):
    __tablename__ = "facturas"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_factura: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    id_orden: Mapped[str] = mapped_column(String(12), ForeignKey("ordenes_servicio.id_orden"), index=True)
    id_cliente: Mapped[str] = mapped_column(String(12), ForeignKey("clientes.id_cliente"))
    mano_obra: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    repuestos: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    descuentos: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    base_iva: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    impuestos: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    saldo_pendiente: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    estado: Mapped[str] = mapped_column(String(10))
    fecha_emision: Mapped[datetime] = mapped_column(DateTime(timezone=True))
