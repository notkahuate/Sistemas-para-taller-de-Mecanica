"""Modelo de base de datos de repuestos (tabla repuestos)."""
from decimal import Decimal

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RepuestoModel(Base):
    __tablename__ = "repuestos"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_repuesto: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    referencia: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    id_categoria: Mapped[str] = mapped_column(String(10))
    id_proveedor: Mapped[str | None] = mapped_column(String(20), nullable=True)
    costo: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_minimo: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(10), default="activo")
