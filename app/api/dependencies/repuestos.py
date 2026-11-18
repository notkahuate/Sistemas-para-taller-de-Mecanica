"""Dependencias inyectables del módulo de repuestos."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.repuesto_repository import RepuestoRepository
from app.services.repuesto_service import RepuestoService


def get_repuesto_service(db: Session = Depends(get_db)) -> RepuestoService:
    return RepuestoService(RepuestoRepository(db))
