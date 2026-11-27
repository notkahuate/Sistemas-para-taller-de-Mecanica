"""Endpoints de pagos (MOD-05, SUB-14). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.pagos import get_pago_cliente_service
from app.api.schemas.pago_cliente import PagoClienteCrear, PagoClienteRegistrado
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_RECEPCION
from app.services.pago_cliente_service import PagoClienteService

router = APIRouter(prefix="/api/v1/pagos", tags=["MOD-05 Pagos"])


@router.post(
    "/clientes",
    status_code=201,
    summary="HU-066 Registrar pago de cliente",
    description=(
        "Registra un pago (efectivo, transferencia, tarjeta u otros) sobre una factura emitida o pagada_parcial y "
        "reduce su saldo. Si el valor iguala el saldo la factura queda pagada; si es menor, pagada_parcial. "
        "Valor mayor que el saldo: 409 RN-11; factura anulada: 409 VAL-NEGOCIO."
    ),
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
)
def registrar_pago_cliente(
    body: PagoClienteCrear, servicio: PagoClienteService = Depends(get_pago_cliente_service)
):
    pago, factura = servicio.registrar(body.model_dump())
    data = PagoClienteRegistrado(
        id_pago=pago.id_pago,
        id_factura=pago.id_factura,
        valor=pago.valor,
        saldo_pendiente=factura.saldo_pendiente,
        estado_factura=factura.estado,
        metodo=pago.metodo,
        referencia_comprobante=pago.referencia_comprobante,
    ).model_dump(by_alias=True)
    return envelope(success=True, message="Pago de cliente registrado correctamente", data=data, status_code=201)
