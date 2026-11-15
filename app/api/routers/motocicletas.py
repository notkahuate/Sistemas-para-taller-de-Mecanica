"""Endpoints de motocicletas (MOD-01, SUB-02). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.motocicletas import get_motocicleta_service
from app.api.schemas.motocicleta import MotocicletaCrear, MotocicletaRegistrada
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_RECEPCION
from app.services.motocicleta_service import MotocicletaService

router = APIRouter(prefix="/api/v1/motocicletas", tags=["MOD-01 Motocicletas"])


@router.post(
    "",
    status_code=201,
    summary="HU-006 Registrar motocicleta",
    description="Registra una motocicleta de un cliente activo (RN-01). La placa no se puede repetir (RN-12).",
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
)
def registrar_motocicleta(body: MotocicletaCrear, servicio: MotocicletaService = Depends(get_motocicleta_service)):
    motocicleta = servicio.registrar(body.model_dump())
    data = MotocicletaRegistrada.model_validate(motocicleta).model_dump(by_alias=True)
    return envelope(success=True, message="Motocicleta registrada correctamente", data=data, status_code=201)
