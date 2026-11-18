"""Endpoints de órdenes de servicio (MOD-02, SUB-04). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.ordenes_servicio import get_orden_servicio_service
from app.api.schemas.orden_servicio import OrdenServicioCrear, OrdenServicioRegistrada
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_RECEPCION
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
