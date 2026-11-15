"""Dependencias inyectables del módulo de motocicletas."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.motocicleta_repository import MotocicletaRepository
from app.services.motocicleta_service import MotocicletaService


def get_motocicleta_service(db: Session = Depends(get_db)) -> MotocicletaService:
    return MotocicletaService(MotocicletaRepository(db), ClienteRepository(db))
