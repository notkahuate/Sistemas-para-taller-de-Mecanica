"""Endpoints de motocicletas (MOD-01, SUB-02). Solo reciben la petición, llaman al servicio y responden."""
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.motocicletas import get_motocicleta_service
from app.api.schemas.motocicleta import MotocicletaCrear, MotocicletaDetalle, MotocicletaRegistrada
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_RECEPCION
from app.domain.entities.motocicleta import Motocicleta
from app.services.motocicleta_service import MotocicletaService

router = APIRouter(prefix="/api/v1/motocicletas", tags=["MOD-01 Motocicletas"])

MSG_CONSULTA_EXITOSA = "Consulta de motocicleta exitosa"


def _detalle(motocicleta: Motocicleta, nombre_propietario: str | None) -> dict:
    return MotocicletaDetalle(**asdict(motocicleta), nombre_propietario=nombre_propietario).model_dump(by_alias=True)


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


@router.get(
    "",
    summary="HU-007 Consultar motocicleta por placa",
    description="Devuelve la motocicleta con esa placa, su propietario y su estado. La placa se normaliza a mayúsculas.",
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
)
def consultar_motocicleta_por_placa(
    placa: str | None = Query(default=None, examples=["ABC12D"]),
    servicio: MotocicletaService = Depends(get_motocicleta_service),
):
    motocicleta, propietario = servicio.consultar_por_placa(placa)
    return envelope(success=True, message=MSG_CONSULTA_EXITOSA, data=_detalle(motocicleta, propietario))


@router.get(
    "/{id_motocicleta}",
    summary="HU-007 Consultar motocicleta",
    description="Devuelve la motocicleta por su idMotocicleta (formato MTO-NNNN), con su propietario, datos técnicos y estado.",
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
)
def consultar_motocicleta(id_motocicleta: str, servicio: MotocicletaService = Depends(get_motocicleta_service)):
    motocicleta, propietario = servicio.consultar_por_id(id_motocicleta)
    return envelope(success=True, message=MSG_CONSULTA_EXITOSA, data=_detalle(motocicleta, propietario))
