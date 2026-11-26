"""Caso de uso HU-030 Registrar tiempo de mano de obra."""
import re
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.core.responses import ahora_bogota
from app.domain.entities.actividad_mantenimiento import (
    MINUTOS_MAX,
    MINUTOS_MIN,
    TOLERANCIA_HORA_INICIO_MIN,
    ActividadMantenimiento,
)
from app.domain.entities.orden_servicio import ESTADO_EN_PROCESO, ESTADO_FINALIZADA
from app.domain.exceptions.errors import NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.actividad_mantenimiento_repository import IActividadMantenimientoRepository
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository
from app.domain.interfaces.tecnico_repository import ITecnicoRepository
from app.services.orden_servicio_service import DatosOrdenInvalidosError

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar tiempo de mano de obra»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar tiempo de mano de obra»: la operación viola una regla de negocio."
ID_ACTIVIDAD_RE = re.compile(r"^ACT-\d{4}$")


def calcular_valor(minutos: int, tarifa_horaria: Decimal) -> Decimal:
    """valorManoObra = round(minutos / 60 * tarifaHoraria, 2)."""
    return (Decimal(minutos) / Decimal(60) * tarifa_horaria).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ManoObraService:
    def __init__(
        self,
        actividades: IActividadMantenimientoRepository,
        ordenes: IOrdenServicioRepository,
        tecnicos: ITecnicoRepository,
    ):
        self.actividades = actividades
        self.ordenes = ordenes
        self.tecnicos = tecnicos

    def _validar_formato(self, id_actividad: str, datos: dict) -> int:
        def error(campo: str, detalle: str):
            return DatosOrdenInvalidosError(MSG_DATOS_INVALIDOS, "VAL-FORMATO", detalle, campo)

        if not ID_ACTIVIDAD_RE.match(id_actividad):
            raise error("idActividad", "Formato de idActividad no válido. Debe ser ACT-NNNN.")
        inicio, fin = datos["hora_inicio"], datos["hora_fin"]
        for campo, hora in (("horaInicio", inicio), ("horaFin", fin)):
            if hora.tzinfo is None:
                raise error(campo, f"{campo} debe incluir el offset, por ejemplo -05:00.")
        if fin <= inicio:
            raise error("horaFin", "horaFin debe ser posterior a horaInicio.")
        if fin > ahora_bogota() + timedelta(minutes=TOLERANCIA_HORA_INICIO_MIN):
            raise error("horaFin", "horaFin no puede ser posterior a la hora actual más 10 minutos.")
        minutos = int((fin - inicio).total_seconds() // 60)
        if not MINUTOS_MIN <= minutos <= MINUTOS_MAX:
            raise error("request", "Minutos fuera de rango")
        return minutos

    def registrar(self, id_actividad: str, datos: dict) -> ActividadMantenimiento:
        minutos = self._validar_formato(id_actividad, datos)

        actividad = self.actividades.obtener_por_id(id_actividad)
        if actividad is None:
            raise NoEncontradoError("No existe una actividad para el identificador indicado", "idActividad")
        orden = self.ordenes.obtener_por_id(actividad.id_orden)

        # RN-02: el tiempo se registra mientras la orden está en_proceso.
        if orden.estado == ESTADO_FINALIZADA:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-02", "Orden finalizada", "request")
        if orden.estado != ESTADO_EN_PROCESO:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-02", "Orden no está en_proceso", "request")

        # La tarifa se lee del técnico de la actividad; no viene en el body.
        tecnico = self.tecnicos.obtener_por_id(actividad.id_tecnico)
        tarifa: Decimal = tecnico.tarifa_horaria
        return self.actividades.registrar_mano_obra(
            actividad.id_actividad,
            {
                "hora_inicio": datos["hora_inicio"],
                "hora_fin": datos["hora_fin"],
                "minutos": minutos,
                "tarifa_horaria": tarifa,
                "valor_mano_obra": calcular_valor(minutos, tarifa),  # RN-05: alimenta la factura
            },
        )
