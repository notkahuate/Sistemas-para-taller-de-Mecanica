"""Dependencias inyectables del módulo de técnicos."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.tecnico_repository import TecnicoRepository
from app.services.tecnico_service import TecnicoService


def get_tecnico_service(db: Session = Depends(get_db)) -> TecnicoService:
    return TecnicoService(TecnicoRepository(db))
