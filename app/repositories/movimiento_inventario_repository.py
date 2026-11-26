"""Repositorio de movimientos de inventario. El stock siempre se calcula sumando movimientos."""
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.domain.entities.movimiento_inventario import TIPO_ENTRADA, MovimientoInventario, generar_id_movimiento
from app.domain.interfaces.movimiento_inventario_repository import IMovimientoInventarioRepository
from app.domain.models.movimiento_inventario import MovimientoInventarioModel


def a_entidad(m: MovimientoInventarioModel) -> MovimientoInventario:
    return MovimientoInventario(
        id_movimiento=m.id_movimiento or "",
        id_repuesto=m.id_repuesto,
        referencia=m.referencia,
        tipo=m.tipo,
        motivo=m.motivo,
        cantidad=m.cantidad,
        stock_resultante=m.stock_resultante,
        id_recepcion=m.id_recepcion,
        ubicacion=m.ubicacion,
        usuario=m.usuario,
        fecha=m.fecha,
    )


class MovimientoInventarioRepository(IMovimientoInventarioRepository):
    def __init__(self, db: Session):
        self.db = db

    def stock_actual(self, id_repuesto: str) -> Decimal:
        signo = case((MovimientoInventarioModel.tipo == TIPO_ENTRADA, 1), else_=-1)
        consulta = select(func.coalesce(func.sum(signo * MovimientoInventarioModel.cantidad), 0)).where(
            MovimientoInventarioModel.id_repuesto == id_repuesto
        )
        return Decimal(str(self.db.scalar(consulta))).quantize(Decimal("0.001"))

    def registrar(self, datos: dict) -> MovimientoInventario:
        """Guarda el movimiento con el saldo resultante calculado en la misma transacción."""
        try:
            saldo = self.stock_actual(datos["id_repuesto"])
            cantidad = datos["cantidad"] if datos["tipo"] == TIPO_ENTRADA else -datos["cantidad"]
            modelo = MovimientoInventarioModel(**datos, stock_resultante=saldo + cantidad)
            self.db.add(modelo)
            self.db.flush()  # obtiene la secuencia para armar el idMovimiento
            modelo.id_movimiento = generar_id_movimiento(modelo.secuencia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)
