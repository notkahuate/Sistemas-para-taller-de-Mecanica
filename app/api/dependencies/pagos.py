"""Dependencias del módulo de pagos."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.factura_repository import FacturaRepository
from app.repositories.pago_cliente_repository import PagoClienteRepository
from app.services.pago_cliente_service import PagoClienteService


def get_pago_cliente_service(db: Session = Depends(get_db)) -> PagoClienteService:
    return PagoClienteService(FacturaRepository(db), PagoClienteRepository(db))
