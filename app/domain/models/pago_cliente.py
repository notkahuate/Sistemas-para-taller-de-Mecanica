"""Modelo de base de datos de pagos de clientes (tabla pagos_clientes)."""
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PagoClienteModel(Base):
    __tablename__ = "pagos_clientes"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_pago: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    id_factura: Mapped[str] = mapped_column(String(12), ForeignKey("facturas.id_factura"), index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    fecha_pago: Mapped[date] = mapped_column(Date)
    metodo: Mapped[str] = mapped_column(String(15))
    referencia_comprobante: Mapped[str] = mapped_column(String(40))
