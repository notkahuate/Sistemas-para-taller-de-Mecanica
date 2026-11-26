"""Endpoints de órdenes de servicio (MOD-02, SUB-04). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.ordenes_servicio import (
    get_actividad_service,
    get_consumo_service,
    get_diagnostico_service,
    get_orden_servicio_service,
)
from app.api.schemas.actividad_mantenimiento import ActividadCrear, ActividadRegistrada
from app.api.schemas.consumo_repuesto import ConsumoCrear, ConsumoRegistrado
from app.api.schemas.diagnostico_tecnico import DiagnosticoCrear, DiagnosticoRegistrado
from app.api.schemas.orden_servicio import (
    AsignacionTecnico,
    EstadoOrden,
    OrdenServicioCrear,
    OrdenServicioRegistrada,
    TecnicoAsignar,
)
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_RECEPCION, ROL_TECNICO
from app.services.actividad_mantenimiento_service import ActividadMantenimientoService
from app.services.consumo_repuesto_service import ConsumoRepuestoService
from app.services.diagnostico_tecnico_service import DiagnosticoTecnicoService
from app.services.orden_servicio_service import OrdenServicioService

router = APIRouter(prefix="/api/v1/ordenes-servicio", tags=["MOD-02 Órdenes de servicio"])


@router.post(
    "",
    status_code=201,
    summary="HU-016 Registrar orden de servicio",
    description=(
        "Abre una orden en estado recibida para una moto de un cliente activo (RN-01). "
        "La moto debe pertenecer al cliente y no puede tener otra orden abierta."
    ),
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
)
def registrar_orden(body: OrdenServicioCrear, servicio: OrdenServicioService = Depends(get_orden_servicio_service)):
    orden = servicio.registrar(body.model_dump())
    data = OrdenServicioRegistrada.model_validate(orden).model_dump(by_alias=True)
    return envelope(success=True, message="Orden de servicio registrada correctamente", data=data, status_code=201)


@router.patch(
    "/{idOrden}/tecnico",
    summary="HU-017 Asignar técnico a la orden",
    description=(
        "Asigna un técnico activo a una orden recibida o en proceso y la deja en en_proceso. "
        "Si la orden está finalizada responde 409 RN-02; si el técnico no está activo, 409 RN-06. "
        "En el MVP RN-06 solo valida que el técnico esté activo; especialidad y disponibilidad quedan para v2."
    ),
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
)
def asignar_tecnico(
    idOrden: str,  # noqa: N803  (el contrato usa camelCase en la ruta)
    body: TecnicoAsignar,
    servicio: OrdenServicioService = Depends(get_orden_servicio_service),
):
    orden, tecnico = servicio.asignar_tecnico(idOrden, body.model_dump())
    data = AsignacionTecnico(
        id_orden=orden.id_orden,
        id_tecnico=orden.id_tecnico,
        nombre_tecnico=tecnico.nombre_completo,
        id_especialidad_requerida=orden.id_especialidad_requerida,
        estado=orden.estado,
        fecha_asignacion=orden.fecha_asignacion,
    ).model_dump(by_alias=True)
    return envelope(success=True, message="Técnico asignado a la orden correctamente", data=data)


@router.post(
    "/{idOrden}/actividades",
    status_code=201,
    summary="HU-026 Registrar actividades de mantenimiento",
    description=(
        "Registra una actividad (pendiente, en_ejecucion o completada) sobre una orden en_proceso. "
        "El técnico se toma del asignado a la orden (HU-017). Si la orden está finalizada responde 409 RN-02."
    ),
    dependencies=[Depends(requiere_rol(ROL_TECNICO, ROL_ADMINISTRADOR))],
)
def registrar_actividad(
    idOrden: str,  # noqa: N803  (el contrato usa camelCase en la ruta)
    body: ActividadCrear,
    servicio: ActividadMantenimientoService = Depends(get_actividad_service),
):
    actividad = servicio.registrar(idOrden, body.model_dump())
    data = ActividadRegistrada.model_validate(actividad).model_dump(by_alias=True)
    return envelope(success=True, message="Actividad de mantenimiento registrada correctamente", data=data, status_code=201)


@router.get(
    "/{idOrden}",
    summary="HU-018 Consultar estado de la orden",
    description=(
        "Devuelve el estado de la orden (recibida, en_proceso o finalizada) y el resumen de avance: "
        "técnico asignado, actividades registradas, diagnóstico y repuestos consumidos."
    ),
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_TECNICO, ROL_ADMINISTRADOR))],
)
def consultar_orden(
    idOrden: str,  # noqa: N803  (el contrato usa camelCase en la ruta)
    servicio: OrdenServicioService = Depends(get_orden_servicio_service),
):
    r = servicio.consultar(idOrden)
    o = r["orden"]
    data = EstadoOrden(
        id_orden=o.id_orden,
        id_cliente=o.id_cliente,
        id_motocicleta=o.id_motocicleta,
        placa=r["placa"],
        estado=o.estado,
        id_tecnico=o.id_tecnico,
        motivo_visita=o.motivo_visita,
        fecha_ingreso=o.fecha_ingreso,
        fecha_cierre=o.fecha_cierre,
        tiene_diagnostico=r["tiene_diagnostico"],
        actividades_registradas=r["actividades_registradas"],
        repuestos_consumidos=r["repuestos_consumidos"],
    ).model_dump(by_alias=True)
    return envelope(success=True, message="Consulta de orden de servicio exitosa", data=data)


@router.post(
    "/{idOrden}/diagnosticos",
    status_code=201,
    summary="HU-021 Registrar diagnóstico técnico",
    description=(
        "Registra el diagnóstico técnico de una orden en_proceso: hallazgos, pruebas y diagnóstico "
        "(mínimo 15 caracteres cada uno) y recomendaciones. Una orden admite un solo diagnóstico vigente."
    ),
    dependencies=[Depends(requiere_rol(ROL_TECNICO, ROL_ADMINISTRADOR))],
)
def registrar_diagnostico(
    idOrden: str,  # noqa: N803  (el contrato usa camelCase en la ruta)
    body: DiagnosticoCrear,
    servicio: DiagnosticoTecnicoService = Depends(get_diagnostico_service),
):
    diagnostico = servicio.registrar(idOrden, body.model_dump())
    data = DiagnosticoRegistrado.model_validate(diagnostico).model_dump(by_alias=True)
    return envelope(success=True, message="Diagnóstico técnico registrado correctamente", data=data, status_code=201)


@router.post(
    "/{idOrden}/repuestos-utilizados",
    status_code=201,
    summary="HU-027 Registrar repuestos utilizados",
    description=(
        "Asocia referencia y cantidad a una actividad de la orden en_proceso, descuenta el stock con un movimiento "
        "SALIDA motivo consumo_orden y devuelve el saldo. Si el stock no alcanza responde 409 RN-03."
    ),
)
def registrar_repuestos_utilizados(
    idOrden: str,  # noqa: N803  (el contrato usa camelCase en la ruta)
    body: ConsumoCrear,
    usuario: dict = Depends(requiere_rol(ROL_TECNICO, ROL_ADMINISTRADOR)),
    servicio: ConsumoRepuestoService = Depends(get_consumo_service),
):
    consumo = servicio.registrar(idOrden, body.model_dump(), usuario["usuario"])
    data = ConsumoRegistrado.model_validate(consumo).model_dump(by_alias=True)
    return envelope(success=True, message="Repuestos utilizados registrados correctamente", data=data, status_code=201)
