"""Endpoints de repuestos (MOD-03, SUB-07). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.repuestos import get_repuesto_service
from app.api.schemas.repuesto import RepuestoCrear, RepuestoRegistrado
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_INVENTARIO
from app.services.repuesto_service import RepuestoService

router = APIRouter(prefix="/api/v1/repuestos", tags=["MOD-03 Repuestos"])


@router.post(
    "",
    status_code=201,
    summary="HU-031 Registrar repuesto",
    description=(
        "Registra un repuesto activo con stock 0. La referencia es única y el precio debe ser mayor o igual al costo. "
        "Categorías: CAT-MOT, CAT-FRE, CAT-ELE, CAT-TRA, CAT-SUS, CAT-OTR. El proveedor es opcional."
    ),
    dependencies=[Depends(requiere_rol(ROL_INVENTARIO, ROL_ADMINISTRADOR))],
)
def registrar_repuesto(body: RepuestoCrear, servicio: RepuestoService = Depends(get_repuesto_service)):
    repuesto = servicio.registrar(body.model_dump())
    data = RepuestoRegistrado.model_validate(repuesto).model_dump(by_alias=True)
    return envelope(success=True, message="Repuesto registrado correctamente", data=data, status_code=201)
