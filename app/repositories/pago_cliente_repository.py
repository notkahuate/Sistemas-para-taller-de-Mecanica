"""Repositorio de pagos de clientes: guarda el pago y el nuevo saldo de la factura juntos."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.factura import Factura
from app.domain.entities.pago_cliente import PagoCliente, generar_id_pago
from app.domain.interfaces.pago_cliente_repository import IPagoClienteRepository
from app.domain.models.factura import FacturaModel
from app.domain.models.pago_cliente import PagoClienteModel
from app.repositories.factura_repository import a_entidad as factura_a_entidad


def a_entidad(m: PagoClienteModel) -> PagoCliente:
    return PagoCliente(
        id_pago=m.id_pago or "",
        id_factura=m.id_factura,
        valor=m.valor,
        fecha_pago=m.fecha_pago,
        metodo=m.metodo,
        referencia_comprobante=m.referencia_comprobante,
    )


class PagoClienteRepository(IPagoClienteRepository):
    def __init__(self, db: Session):
        self.db = db

    def registrar(self, pago: dict, saldo_pendiente: Decimal, estado_factura: str) -> tuple[PagoCliente, Factura]:
        factura = self.db.scalar(select(FacturaModel).where(FacturaModel.id_factura == pago["id_factura"]))
        modelo = PagoClienteModel(**pago)
        try:
            self.db.add(modelo)
            self.db.flush()  # obtiene la secuencia para armar el idPago
            modelo.id_pago = generar_id_pago(modelo.secuencia)
            factura.saldo_pendiente = saldo_pendiente
            factura.estado = estado_factura
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        self.db.refresh(factura)
        return a_entidad(modelo), factura_a_entidad(factura)
