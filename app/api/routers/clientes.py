"""Endpoints de clientes (MOD-01). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.clientes import get_cliente_service
from app.api.schemas.cliente import ClienteCrear, ClienteDetalle, ClienteRegistrado
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_RECEPCION
from app.services.cliente_service import ClienteService

router = APIRouter(prefix="/api/v1/clientes", tags=["MOD-01 Clientes"])


@router.post(
    "",
    status_code=201,
    summary="HU-001 Registrar cliente",
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
    description="Registra un cliente nuevo en estado activo. El número de documento no se puede repetir (RN-12).",
)
def registrar_cliente(body: ClienteCrear, servicio: ClienteService = Depends(get_cliente_service)):
    cliente = servicio.registrar(body.model_dump())
    data = ClienteRegistrado.model_validate(cliente).model_dump(by_alias=True)
    return envelope(success=True, message="Cliente registrado correctamente", data=data, status_code=201)


@router.get(
    "/{id_cliente}",
    summary="HU-002 Consultar cliente",
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
    description="Devuelve la ficha de un cliente por su idCliente (formato CLI-NNNN). Incluye clientes inactivos.",
)
def consultar_cliente(id_cliente: str, servicio: ClienteService = Depends(get_cliente_service)):
    cliente = servicio.consultar(id_cliente)
    data = ClienteDetalle.model_validate(cliente).model_dump(by_alias=True)
    return envelope(success=True, message="Consulta de cliente exitosa", data=data)
