"""Caso de uso HU-021 Registrar diagnóstico técnico."""
from app.core.responses import ahora_bogota
from app.domain.entities.diagnostico_tecnico import ESTADO_REGISTRADO, DiagnosticoTecnico
from app.domain.entities.orden_servicio import ESTADO_EN_PROCESO
from app.domain.exceptions.errors import NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.diagnostico_tecnico_repository import IDiagnosticoTecnicoRepository
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository
from app.services.orden_servicio_service import DatosOrdenInvalidosError
from app.services.validators.diagnostico_tecnico_validator import validar_formato_diagnostico

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar diagnóstico técnico»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar diagnóstico técnico»: la operación viola una regla de negocio."


class DiagnosticoTecnicoService:
    def __init__(self, repositorio: IDiagnosticoTecnicoRepository, ordenes: IOrdenServicioRepository):
        self.repositorio = repositorio
        self.ordenes = ordenes

    def registrar(self, id_orden: str, datos: dict) -> DiagnosticoTecnico:
        errores = validar_formato_diagnostico(id_orden, datos)
        if errores:
            campo, codigo, detalle = errores[0]
            raise DatosOrdenInvalidosError(MSG_DATOS_INVALIDOS, codigo, detalle, campo)

        orden = self.ordenes.obtener_por_id(id_orden)
        if orden is None:
            raise NoEncontradoError("No existe una orden de servicio para el identificador indicado", "idOrden")

        # RN-02: el diagnóstico se registra sobre una orden en_proceso (con técnico asignado, HU-017).
        if orden.estado != ESTADO_EN_PROCESO or orden.id_tecnico is None:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-02", "Orden no está en_proceso", "request")
        # Una orden admite un solo diagnóstico vigente; para cambiarlo se usa HU-023.
        if self.repositorio.tiene_vigente(orden.id_orden):
            raise ReglaNegocioError(
                MSG_REGLA_NEGOCIO,
                "DIAG-VIGENTE",
                "La orden ya tiene un diagnóstico vigente; para modificarlo use HU-023",
                "idOrden",
            )

        recomendaciones = datos.get("recomendaciones")
        return self.repositorio.crear(
            {
                "id_orden": orden.id_orden,
                "hallazgos": datos["hallazgos"].strip(),
                "pruebas": datos["pruebas"].strip(),
                "diagnostico": datos["diagnostico"].strip(),
                "recomendaciones": recomendaciones.strip() if recomendaciones else None,
                "estado": ESTADO_REGISTRADO,
                "id_tecnico": orden.id_tecnico,  # el técnico se toma del asignado a la orden
                "fecha_registro": ahora_bogota(),
            }
        )
