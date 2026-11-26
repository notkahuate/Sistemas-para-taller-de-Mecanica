"""Casos de uso de inventario."""
from decimal import Decimal

from app.core.responses import ahora_bogota
from app.domain.entities.movimiento_inventario import MOTIVOS_ENTRADA, TIPO_ENTRADA, MovimientoInventario
from app.domain.entities.repuesto import ESTADO_ACTIVO
from app.domain.exceptions.errors import FormatoInvalidoError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.movimiento_inventario_repository import IMovimientoInventarioRepository
from app.domain.interfaces.repuesto_repository import IRepuestoRepository

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar entrada de stock»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar entrada de stock»: la operación viola una regla de negocio."


class InventarioService:
    def __init__(self, movimientos: IMovimientoInventarioRepository, repuestos: IRepuestoRepository):
        self.movimientos = movimientos
        self.repuestos = repuestos

    def registrar_entrada(self, datos: dict, usuario: str) -> MovimientoInventario:
        """HU-037 Registrar entrada de stock (manual en el MVP)."""
        cantidad: Decimal = datos["cantidad"]
        if cantidad <= 0:
            raise FormatoInvalidoError(MSG_DATOS_INVALIDOS, "Cantidad <= 0", "cantidad")
        if cantidad != cantidad.quantize(Decimal("0.001")):
            raise FormatoInvalidoError(MSG_DATOS_INVALIDOS, "La cantidad admite máximo 3 decimales.", "cantidad")
        if datos["motivo"] not in MOTIVOS_ENTRADA:
            raise FormatoInvalidoError(
                MSG_DATOS_INVALIDOS, f"Motivo no válido. Use: {', '.join(MOTIVOS_ENTRADA)}.", "motivo"
            )
        # RN-04 depende de la recepción de compras (HU-057/HU-059), que no está en el MVP.
        if datos.get("id_recepcion") is not None:
            raise FormatoInvalidoError(
                MSG_DATOS_INVALIDOS,
                "La recepción de compras no está disponible en esta versión; envíe idRecepcion en null.",
                "idRecepcion",
            )

        repuesto = self.repuestos.obtener_por_referencia(datos["referencia"].strip())
        if repuesto is None:
            raise NoEncontradoError("No existe un repuesto con la referencia indicada", "referencia")
        if repuesto.estado != ESTADO_ACTIVO:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "VAL-NEGOCIO", "Repuesto inactivo", "request")

        return self.movimientos.registrar(
            {
                "id_repuesto": repuesto.id_repuesto,
                "referencia": repuesto.referencia,
                "tipo": TIPO_ENTRADA,
                "motivo": datos["motivo"],
                "cantidad": cantidad,
                "id_recepcion": None,
                "ubicacion": (datos.get("ubicacion") or "").strip() or None,
                "usuario": usuario,
                "fecha": ahora_bogota(),
            }
        )
