"""Caso de uso HU-020 Cerrar y facturar orden de servicio (RN-02, RN-05)."""
from app.core.responses import ahora_bogota
from app.domain.entities.factura import ESTADO_EMITIDA, calcular_totales
from app.domain.entities.orden_servicio import ESTADO_EN_PROCESO, ESTADO_FINALIZADA, ID_ORDEN_RE
from app.domain.exceptions.errors import NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.actividad_mantenimiento_repository import IActividadMantenimientoRepository
from app.domain.interfaces.consumo_repuesto_repository import IConsumoRepuestoRepository
from app.domain.interfaces.diagnostico_tecnico_repository import IDiagnosticoTecnicoRepository
from app.domain.interfaces.factura_repository import IFacturaRepository
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository
from app.services.orden_servicio_service import DatosOrdenInvalidosError

MSG_DATOS_INVALIDOS = "No fue posible completar «Cerrar y facturar orden de servicio»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = (
    "No fue posible completar «Cerrar y facturar orden de servicio»: la operación viola una regla de negocio."
)
# El envío por correo o mensajería depende de un proveedor externo que no está integrado en el MVP:
# la notificación queda pendiente y no se informa como enviada.
NOTIFICACION_PENDIENTE = "pendiente"
NOTIFICACION_NO_SOLICITADA = "no_solicitada"


class CierreOrdenService:
    def __init__(
        self,
        ordenes: IOrdenServicioRepository,
        diagnosticos: IDiagnosticoTecnicoRepository,
        actividades: IActividadMantenimientoRepository,
        consumos: IConsumoRepuestoRepository,
        facturas: IFacturaRepository,
    ):
        self.ordenes = ordenes
        self.diagnosticos = diagnosticos
        self.actividades = actividades
        self.consumos = consumos
        self.facturas = facturas

    def cerrar(self, id_orden: str, datos: dict) -> dict:
        if not ID_ORDEN_RE.match(id_orden):
            raise DatosOrdenInvalidosError(
                MSG_DATOS_INVALIDOS, "VAL-FORMATO", "Formato de idOrden no válido. Debe ser OS-NNNN.", "idOrden"
            )
        if datos["confirmar_cierre"] is not True:
            raise DatosOrdenInvalidosError(
                MSG_DATOS_INVALIDOS, "VAL-FORMATO", "Debe confirmar el cierre (confirmarCierre = true).", "confirmarCierre"
            )

        orden = self.ordenes.obtener_por_id(id_orden)
        if orden is None:
            raise NoEncontradoError("No existe una orden de servicio para el identificador indicado", "idOrden")

        # RN-02: una orden finalizada no se vuelve a cerrar; solo se cierra la que está en_proceso.
        if orden.estado == ESTADO_FINALIZADA:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-02", "Orden ya finalizada RN-02", "request")
        if orden.estado != ESTADO_EN_PROCESO:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-02", "Orden no está en_proceso RN-02", "request")
        # RN-05: se factura solo lo ejecutado: diagnóstico vigente y al menos una actividad completada.
        if not self.diagnosticos.tiene_vigente(orden.id_orden) or self.actividades.contar_completadas(orden.id_orden) == 0:
            raise ReglaNegocioError(
                MSG_REGLA_NEGOCIO, "RN-05", "Sin diagnóstico o actividades incompletas RN-05", "request"
            )
        if self.facturas.tiene_vigente(orden.id_orden):
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-05", "La orden ya tiene una factura vigente", "request")

        totales = calcular_totales(
            mano_obra=self.actividades.total_mano_obra(orden.id_orden),
            repuestos=self.consumos.total_repuestos(orden.id_orden),
        )
        ahora = ahora_bogota()
        orden, factura = self.ordenes.cerrar_y_facturar(
            orden.id_orden,
            ahora,
            {**totales, "saldo_pendiente": totales["total"], "estado": ESTADO_EMITIDA, "fecha_emision": ahora},
        )
        return {
            "orden": orden,
            "factura": factura,
            "notificacion": NOTIFICACION_PENDIENTE if datos["notificar_cliente"] else NOTIFICACION_NO_SOLICITADA,
        }
