"""Dependencias inyectables del módulo de clientes."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.cliente_repository import ClienteRepository
from app.services.cliente_service import ClienteService


def get_cliente_service(db: Session = Depends(get_db)) -> ClienteService:
    return ClienteService(ClienteRepository(db))
