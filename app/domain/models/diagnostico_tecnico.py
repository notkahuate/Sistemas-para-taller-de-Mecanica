"""Modelo de base de datos de diagnósticos técnicos (tabla diagnosticos_tecnicos)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DiagnosticoTecnicoModel(Base):
    __tablename__ = "diagnosticos_tecnicos"

    secuencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_diagnostico: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    id_orden: Mapped[str] = mapped_column(String(12), ForeignKey("ordenes_servicio.id_orden"), index=True)
    hallazgos: Mapped[str] = mapped_column(Text)
    pruebas: Mapped[str] = mapped_column(Text)
    diagnostico: Mapped[str] = mapped_column(Text)
    recomendaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(15))
    id_tecnico: Mapped[str] = mapped_column(String(12))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True))
