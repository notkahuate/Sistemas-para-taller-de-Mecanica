"""Endpoints de clientes (MOD-01). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.clientes import get_cliente_service
from app.api.schemas.cliente import ClienteCrear, ClienteRegistrado
from app.core.responses import envelope
from app.services.cliente_service import ClienteService

router = APIRouter(prefix="/api/v1/clientes", tags=["MOD-01 Clientes"])


@router.post(
    "",
    status_code=201,
    summary="HU-001 Registrar cliente",
    description="Registra un cliente nuevo en estado activo. El número de documento no se puede repetir (RN-12).",
)
def registrar_cliente(body: ClienteCrear, servicio: ClienteService = Depends(get_cliente_service)):
    cliente = servicio.registrar(body.model_dump())
    data = ClienteRegistrado.model_validate(cliente).model_dump(by_alias=True)
    return envelope(success=True, message="Cliente registrado correctamente", data=data, status_code=201)
