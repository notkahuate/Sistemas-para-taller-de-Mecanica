"""Repositorio de repuestos consumidos: guarda el consumo y su salida de inventario juntos."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.consumo_repuesto import ConsumoRepuesto, generar_id_consumo
from app.domain.entities.movimiento_inventario import TIPO_SALIDA, generar_id_movimiento
from app.domain.interfaces.consumo_repuesto_repository import IConsumoRepuestoRepository
from app.domain.models.consumo_repuesto import ConsumoRepuestoModel
from app.domain.models.movimiento_inventario import MovimientoInventarioModel
from app.repositories.movimiento_inventario_repository import MovimientoInventarioRepository


class ConsumoRepuestoRepository(IConsumoRepuestoRepository):
    def __init__(self, db: Session):
        self.db = db

    def registrar(self, consumo: dict, movimiento: dict) -> ConsumoRepuesto:
        try:
            # Salida de inventario (HU-038/HU-041): el saldo se calcula desde los movimientos.
            saldo = MovimientoInventarioRepository(self.db).stock_actual(movimiento["id_repuesto"])
            mov = MovimientoInventarioModel(**movimiento, tipo=TIPO_SALIDA, stock_resultante=saldo - movimiento["cantidad"])
            self.db.add(mov)
            self.db.flush()
            mov.id_movimiento = generar_id_movimiento(mov.secuencia)

            modelo = ConsumoRepuestoModel(**consumo, id_movimiento=mov.id_movimiento)
            self.db.add(modelo)
            self.db.flush()
            modelo.id_consumo = generar_id_consumo(modelo.secuencia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        self.db.refresh(mov)
        return ConsumoRepuesto(
            id_consumo=modelo.id_consumo,
            id_orden=modelo.id_orden,
            id_actividad=modelo.id_actividad,
            id_repuesto=modelo.id_repuesto,
            referencia=modelo.referencia,
            cantidad=modelo.cantidad,
            precio_unitario=modelo.precio_unitario,
            id_movimiento=mov.id_movimiento,
            stock_resultante=mov.stock_resultante,
            usuario=modelo.usuario,
            fecha=modelo.fecha,
        )

    def contar_por_orden(self, id_orden: str) -> int:
        consulta = select(func.count()).where(ConsumoRepuestoModel.id_orden == id_orden)
        return self.db.scalar(consulta) or 0
