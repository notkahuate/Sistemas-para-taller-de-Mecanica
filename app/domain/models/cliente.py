"""Modelo de base de datos de clientes (tabla clientes)."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ClienteModel(Base):
    __tablename__ = "clientes"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_cliente: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    tipo_documento: Mapped[str] = mapped_column(String(3))
    numero_documento: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(120))
    telefono: Mapped[str] = mapped_column(String(10))
    correo: Mapped[str] = mapped_column(String(120))
    direccion: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(10), default="activo")
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_modificacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
