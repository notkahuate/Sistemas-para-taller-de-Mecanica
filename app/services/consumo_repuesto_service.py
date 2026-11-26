"""Caso de uso HU-027 Registrar repuestos utilizados (cruza MOD-02 y MOD-03)."""
import re
from decimal import Decimal

from app.core.responses import ahora_bogota
from app.domain.entities.consumo_repuesto import MOTIVO_CONSUMO_ORDEN, ConsumoRepuesto
from app.domain.entities.orden_servicio import ESTADO_EN_PROCESO, ESTADO_FINALIZADA, ID_ORDEN_RE
from app.domain.entities.repuesto import ESTADO_ACTIVO
from app.domain.exceptions.errors import NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.actividad_mantenimiento_repository import IActividadMantenimientoRepository
from app.domain.interfaces.consumo_repuesto_repository import IConsumoRepuestoRepository
from app.domain.interfaces.movimiento_inventario_repository import IMovimientoInventarioRepository
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository
from app.domain.interfaces.repuesto_repository import IRepuestoRepository
from app.services.orden_servicio_service import DatosOrdenInvalidosError

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar repuestos utilizados»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar repuestos utilizados»: la operación viola una regla de negocio."
ID_ACTIVIDAD_RE = re.compile(r"^ACT-\d{4}$")


def _numero(valor: Decimal) -> str:
    valor = valor.quantize(Decimal("0.001")).normalize()
    return f"{valor:f}"


class ConsumoRepuestoService:
    def __init__(
        self,
        consumos: IConsumoRepuestoRepository,
        ordenes: IOrdenServicioRepository,
        actividades: IActividadMantenimientoRepository,
        repuestos: IRepuestoRepository,
        movimientos: IMovimientoInventarioRepository,
    ):
        self.consumos = consumos
        self.ordenes = ordenes
        self.actividades = actividades
        self.repuestos = repuestos
        self.movimientos = movimientos

    def _validar_formato(self, id_orden: str, datos: dict) -> None:
        errores: list[tuple[str, str]] = []
        cantidad: Decimal = datos["cantidad"]
        if not ID_ORDEN_RE.match(id_orden):
            errores.append(("idOrden", "Formato de idOrden no válido. Debe ser OS-NNNN."))
        if not ID_ACTIVIDAD_RE.match(datos["id_actividad"]):
            errores.append(("idActividad", "Formato de idActividad no válido. Debe ser ACT-NNNN."))
        if not datos["referencia"].strip():
            errores.append(("referencia", "La referencia es obligatoria."))
        if cantidad <= 0:
            errores.append(("cantidad", "Cantidad <= 0"))
        elif cantidad != cantidad.quantize(Decimal("0.001")):
            errores.append(("cantidad", "La cantidad admite máximo 3 decimales."))
        if datos["motivo"] != MOTIVO_CONSUMO_ORDEN:
            errores.append(("motivo", f"Motivo no válido. Use {MOTIVO_CONSUMO_ORDEN}."))
        if errores:
            campo, detalle = errores[0]
            raise DatosOrdenInvalidosError(MSG_DATOS_INVALIDOS, "VAL-FORMATO", detalle, campo)

    def registrar(self, id_orden: str, datos: dict, usuario: str) -> ConsumoRepuesto:
        self._validar_formato(id_orden, datos)

        orden = self.ordenes.obtener_por_id(id_orden)
        if orden is None:
            raise NoEncontradoError("No existe una orden de servicio para el identificador indicado", "idOrden")
        actividad = self.actividades.obtener_por_id(datos["id_actividad"])
        if actividad is None or actividad.id_orden != orden.id_orden:
            raise NoEncontradoError("No existe esa actividad en la orden indicada", "idActividad")
        repuesto = self.repuestos.obtener_por_referencia(datos["referencia"].strip())
        if repuesto is None:
            raise NoEncontradoError("No existe un repuesto con la referencia indicada", "referencia")

        # RN-02: solo se consumen repuestos en una orden en_proceso.
        if orden.estado == ESTADO_FINALIZADA:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-02", "Orden finalizada RN-02", "request")
        if orden.estado != ESTADO_EN_PROCESO:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-02", "Orden no está en_proceso RN-02", "request")
        if repuesto.estado != ESTADO_ACTIVO:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "VAL-NEGOCIO", "Repuesto inactivo", "request")
        # RN-03: no se despacha lo que no hay en stock.
        cantidad: Decimal = datos["cantidad"]
        stock = self.movimientos.stock_actual(repuesto.id_repuesto)
        if stock < cantidad:
            raise ReglaNegocioError(
                MSG_REGLA_NEGOCIO,
                "RN-03",
                f"Stock insuficiente RN-03: disponible {_numero(stock)}, solicitado {_numero(cantidad)}",
                "cantidad",
            )

        ahora = ahora_bogota()
        return self.consumos.registrar(
            consumo={
                "id_orden": orden.id_orden,
                "id_actividad": actividad.id_actividad,
                "id_repuesto": repuesto.id_repuesto,
                "referencia": repuesto.referencia,
                "cantidad": cantidad,
                "precio_unitario": repuesto.precio,  # precio de venta vigente: alimenta la factura
                "usuario": usuario,
                "fecha": ahora,
            },
            movimiento={
                "id_repuesto": repuesto.id_repuesto,
                "referencia": repuesto.referencia,
                "motivo": MOTIVO_CONSUMO_ORDEN,
                "cantidad": cantidad,
                "id_recepcion": None,
                "ubicacion": None,
                "usuario": usuario,
                "fecha": ahora,
            },
        )
