"""Caso de uso HU-061 Generar factura de servicio (RN-05, RN-11)."""
from app.core.responses import ahora_bogota
from app.domain.entities.cliente import CORREO_RE
from app.domain.entities.factura import ESTADO_EMITIDA, Factura, calcular_totales
from app.domain.entities.orden_servicio import ESTADO_FINALIZADA, ID_ORDEN_RE
from app.domain.exceptions.errors import FormatoInvalidoError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.actividad_mantenimiento_repository import IActividadMantenimientoRepository
from app.domain.interfaces.consumo_repuesto_repository import IConsumoRepuestoRepository
from app.domain.interfaces.factura_repository import IFacturaRepository
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository

MSG_DATOS_INVALIDOS = "No fue posible completar «Generar factura de servicio»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Generar factura de servicio»: la operación viola una regla de negocio."


class FacturaService:
    def __init__(
        self,
        ordenes: IOrdenServicioRepository,
        actividades: IActividadMantenimientoRepository,
        consumos: IConsumoRepuestoRepository,
        facturas: IFacturaRepository,
    ):
        self.ordenes = ordenes
        self.actividades = actividades
        self.consumos = consumos
        self.facturas = facturas

    def generar(self, datos: dict) -> Factura:
        if not ID_ORDEN_RE.match(datos["id_orden"]):
            raise FormatoInvalidoError(MSG_DATOS_INVALIDOS, "Formato de idOrden no válido. Debe ser OS-NNNN.", "idOrden")
        # correoEnvio solo se valida: el envío de la factura es HU-065 y el contrato no lo guarda ni lo devuelve.
        if not CORREO_RE.match(datos["correo_envio"]):
            raise FormatoInvalidoError(MSG_DATOS_INVALIDOS, "Formato de correo no válido.", "correoEnvio")

        orden = self.ordenes.obtener_por_id(datos["id_orden"])
        if orden is None:
            raise NoEncontradoError("No existe una orden de servicio para el identificador indicado", "idOrden")

        # RN-05: solo se factura el servicio ya ejecutado, es decir, la orden finalizada.
        if orden.estado != ESTADO_FINALIZADA:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-05", "Orden no finalizada RN-05", "request")
        # Una factura vigente (no anulada) por orden.
        if self.facturas.tiene_vigente(orden.id_orden):
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "VAL-NEGOCIO", "La orden ya tiene factura emitida", "request")

        # Mano de obra (HU-030) + repuestos (HU-027) + IVA 19%. Los descuentos se aplican en HU-064.
        totales = calcular_totales(
            mano_obra=self.actividades.total_mano_obra(orden.id_orden),
            repuestos=self.consumos.total_repuestos(orden.id_orden),
        )
        return self.facturas.crear(
            {
                **totales,
                "id_orden": orden.id_orden,
                "id_cliente": orden.id_cliente,
                "saldo_pendiente": totales["total"],  # RN-11: la cartera del cliente arranca con el total
                "estado": ESTADO_EMITIDA,
                "fecha_emision": ahora_bogota(),
            }
        )
