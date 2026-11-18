"""Endpoints de inventario (MOD-03, SUB-08). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.inventario import get_inventario_service
from app.api.schemas.inventario import EntradaStockCrear, EntradaStockRegistrada
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_INVENTARIO
from app.services.inventario_service import InventarioService

router = APIRouter(prefix="/api/v1/inventario", tags=["MOD-03 Inventario"])


@router.post(
    "/entradas",
    status_code=201,
    summary="HU-037 Registrar entrada de stock",
    description=(
        "Registra una entrada manual de stock y devuelve el saldo resultante. El stock se calcula siempre desde "
        "los movimientos. Motivos: recepcion_compra, ajuste_positivo, devolucion_cliente. idRecepcion va en null."
    ),
)
def registrar_entrada(
    body: EntradaStockCrear,
    usuario: dict = Depends(requiere_rol(ROL_INVENTARIO, ROL_ADMINISTRADOR)),
    servicio: InventarioService = Depends(get_inventario_service),
):
    movimiento = servicio.registrar_entrada(body.model_dump(), usuario["usuario"])
    data = EntradaStockRegistrada.model_validate(movimiento).model_dump(by_alias=True)
    return envelope(success=True, message="Entrada de stock registrada correctamente", data=data, status_code=201)
