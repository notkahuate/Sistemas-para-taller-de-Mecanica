"""Caso de uso HU-026 Registrar actividades de mantenimiento."""
from app.domain.entities.actividad_mantenimiento import ActividadMantenimiento
from app.domain.entities.orden_servicio import ESTADO_EN_PROCESO, ESTADO_FINALIZADA
from app.domain.exceptions.errors import NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.actividad_mantenimiento_repository import IActividadMantenimientoRepository
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository
from app.services.orden_servicio_service import DatosOrdenInvalidosError
from app.services.validators.actividad_mantenimiento_validator import validar_formato_actividad

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar actividades de mantenimiento»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = (
    "No fue posible completar «Registrar actividades de mantenimiento»: la operación viola una regla de negocio."
)


class ActividadMantenimientoService:
    def __init__(self, repositorio: IActividadMantenimientoRepository, ordenes: IOrdenServicioRepository):
        self.repositorio = repositorio
        self.ordenes = ordenes

    def registrar(self, id_orden: str, datos: dict) -> ActividadMantenimiento:
        errores = validar_formato_actividad(id_orden, datos)
        if errores:
            campo, codigo, detalle = errores[0]
            raise DatosOrdenInvalidosError(MSG_DATOS_INVALIDOS, codigo, detalle, campo)

        orden = self.ordenes.obtener_por_id(id_orden)
        if orden is None:
            raise NoEncontradoError("No existe una orden de servicio para el identificador indicado", "idOrden")

        # RN-02: solo se registran actividades sobre una orden en_proceso (con técnico asignado, HU-017).
        if orden.estado == ESTADO_FINALIZADA:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-02", "Orden finalizada RN-02", "request")
        if orden.estado != ESTADO_EN_PROCESO or orden.id_tecnico is None:
            raise ReglaNegocioError(
                MSG_REGLA_NEGOCIO, "RN-02", "La orden no está en_proceso: falta asignar el técnico RN-02", "request"
            )

        return self.repositorio.crear(
            {
                "id_orden": orden.id_orden,
                "id_tecnico": orden.id_tecnico,  # el técnico se toma del asignado a la orden
                "nombre": datos["nombre"].strip(),
                "estado": datos["estado"],
                "observaciones": datos.get("observaciones"),
                "hora_inicio": datos["hora_inicio"],
                "hora_fin": None,
            }
        )
