"""Modelo de base de datos de técnicos (tabla tecnicos)."""
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TecnicoModel(Base):
    __tablename__ = "tecnicos"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_tecnico: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    tipo_documento: Mapped[str] = mapped_column(String(3))
    numero_documento: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(120))
    telefono: Mapped[str] = mapped_column(String(10))
    correo: Mapped[str] = mapped_column(String(120))
    cargo: Mapped[str] = mapped_column(String(80))
    fecha_ingreso: Mapped[date] = mapped_column(Date)
    tarifa_horaria: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    estado: Mapped[str] = mapped_column(String(10), default="activo")
