"""Modelo de base de datos de motocicletas (tabla motocicletas)."""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MotocicletaModel(Base):
    __tablename__ = "motocicletas"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_motocicleta: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    placa: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    marca: Mapped[str] = mapped_column(String(60))
    linea: Mapped[str] = mapped_column(String(60))
    anio: Mapped[int] = mapped_column(Integer)
    cilindraje: Mapped[int] = mapped_column(Integer)
    color: Mapped[str] = mapped_column(String(30))
    id_cliente: Mapped[str] = mapped_column(String(12), ForeignKey("clientes.id_cliente"), index=True)
    estado: Mapped[str] = mapped_column(String(10), default="activa")
