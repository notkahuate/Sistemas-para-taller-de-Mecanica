"""Endpoints de técnicos (MOD-06, SUB-16). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.tecnicos import get_tecnico_service
from app.api.schemas.tecnico import TecnicoCrear, TecnicoRegistrado
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR
from app.services.tecnico_service import TecnicoService

router = APIRouter(prefix="/api/v1/tecnicos", tags=["MOD-06 Técnicos"])


@router.post(
    "",
    status_code=201,
    summary="HU-076 Registrar técnico",
    description="Registra un técnico activo con su tarifa horaria. El documento no se puede repetir. Solo administrador.",
    dependencies=[Depends(requiere_rol(ROL_ADMINISTRADOR))],
)
def registrar_tecnico(body: TecnicoCrear, servicio: TecnicoService = Depends(get_tecnico_service)):
    tecnico = servicio.registrar(body.model_dump())
    data = TecnicoRegistrado.model_validate(tecnico).model_dump(by_alias=True)
    return envelope(success=True, message="Técnico registrado correctamente", data=data, status_code=201)
