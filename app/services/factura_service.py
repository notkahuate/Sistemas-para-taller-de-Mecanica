"""Casos de uso de facturación: HU-061 Generar factura de servicio y HU-062 Consultar factura."""
from app.core.responses import ahora_bogota
from app.domain.entities.cliente import CORREO_RE
from app.domain.entities.factura import ESTADO_EMITIDA, ID_FACTURA_RE, Factura, calcular_totales
from app.domain.entities.orden_servicio import ESTADO_FINALIZADA, ID_ORDEN_RE
from app.domain.exceptions.errors import FormatoInvalidoError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.actividad_mantenimiento_repository import IActividadMantenimientoRepository
from app.domain.interfaces.consumo_repuesto_repository import IConsumoRepuestoRepository
from app.domain.interfaces.factura_repository import IFacturaRepository
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository

MSG_DATOS_INVALIDOS = "No fue posible completar «Generar factura de servicio»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Generar factura de servicio»: la operación viola una regla de negocio."
MSG_CONSULTA_INVALIDA = "No fue posible completar «Consultar factura»: los datos enviados no son válidos."
MSG_CONSULTA_NO_EXISTE = "No fue posible completar «Consultar factura»: no existe el recurso indicado."


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

    def consultar(self, id_factura: str) -> dict:
        if not ID_FACTURA_RE.match(id_factura):
            raise FormatoInvalidoError(MSG_CONSULTA_INVALIDA, "IdFactura mal formado FAC-NNNN", "request")
        factura = self.facturas.obtener_por_id(id_factura)
        if factura is None:
            raise NoEncontradoError("Factura inexistente", "idFactura", MSG_CONSULTA_NO_EXISTE)

        # RN-05: el detalle muestra lo realmente ejecutado y cobrado en la orden:
        # actividades con tiempo registrado (HU-030) y repuestos consumidos (HU-027).
        mano_obra = [a for a in self.actividades.listar_por_orden(factura.id_orden) if a.minutos is not None]
        return {
            "factura": factura,
            "mano_obra": mano_obra,
            "repuestos": self.consumos.listar_por_orden(factura.id_orden),
            "pagos": [],  # los pagos se registran en HU-066, que aún no existe
        }
