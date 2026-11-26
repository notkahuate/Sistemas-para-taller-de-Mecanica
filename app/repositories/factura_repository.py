"""Repositorio de facturas: único lugar que lee la tabla facturas."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.factura import ESTADO_ANULADA, Factura
from app.domain.interfaces.factura_repository import IFacturaRepository
from app.domain.models.factura import FacturaModel


def a_entidad(m: FacturaModel) -> Factura:
    return Factura(
        id_factura=m.id_factura or "",
        id_orden=m.id_orden,
        id_cliente=m.id_cliente,
        mano_obra=m.mano_obra,
        repuestos=m.repuestos,
        subtotal=m.subtotal,
        descuentos=m.descuentos,
        base_iva=m.base_iva,
        impuestos=m.impuestos,
        total=m.total,
        saldo_pendiente=m.saldo_pendiente,
        estado=m.estado,
        fecha_emision=m.fecha_emision,
    )


class FacturaRepository(IFacturaRepository):
    def __init__(self, db: Session):
        self.db = db

    def tiene_vigente(self, id_orden: str) -> bool:
        consulta = select(FacturaModel.secuencia).where(
            FacturaModel.id_orden == id_orden, FacturaModel.estado != ESTADO_ANULADA
        )
        return self.db.scalar(consulta) is not None
