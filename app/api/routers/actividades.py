"""Endpoints de actividades de mantenimiento (MOD-02, SUB-06). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.actividades import get_mano_obra_service
from app.api.dependencies.auth import requiere_rol
from app.api.schemas.mano_obra import ManoObraRegistrada, ManoObraRegistrar
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_TECNICO
from app.services.mano_obra_service import ManoObraService

router = APIRouter(prefix="/api/v1/actividades", tags=["MOD-02 Órdenes de servicio"])


@router.patch(
    "/{idActividad}/mano-obra",
    summary="HU-030 Registrar tiempo de mano de obra",
    description=(
        "Registra horaInicio y horaFin de la actividad, calcula los minutos (5 a 480) y el valor de mano de obra "
        "con la tarifaHoraria del técnico: round(minutos / 60 * tarifaHoraria, 2). La orden debe estar en_proceso."
    ),
    dependencies=[Depends(requiere_rol(ROL_TECNICO, ROL_ADMINISTRADOR))],
)
def registrar_mano_obra(
    idActividad: str,  # noqa: N803  (el contrato usa camelCase en la ruta)
    body: ManoObraRegistrar,
    servicio: ManoObraService = Depends(get_mano_obra_service),
):
    actividad = servicio.registrar(idActividad, body.model_dump())
    data = ManoObraRegistrada.model_validate(actividad).model_dump(by_alias=True)
    return envelope(success=True, message="Tiempo de mano de obra registrado correctamente", data=data)
