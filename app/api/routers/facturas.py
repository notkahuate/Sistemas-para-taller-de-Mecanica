"""Endpoints de facturación (MOD-05, SUB-13). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.facturas import get_factura_service
from app.api.schemas.factura import FacturaGenerada, FacturaGenerar
from app.core.responses import envelope
from app.domain.entities.usuario import ROL_ADMINISTRADOR, ROL_RECEPCION
from app.services.factura_service import FacturaService

router = APIRouter(prefix="/api/v1/facturas", tags=["MOD-05 Facturación"])


@router.post(
    "",
    status_code=201,
    summary="HU-061 Generar factura de servicio",
    description=(
        "Genera la factura de una orden finalizada sin factura vigente: mano de obra + repuestos - descuentos "
        "+ IVA 19%, en estado emitida y con saldoPendiente igual al total. Orden no finalizada: 409 RN-05; "
        "la orden ya tiene factura emitida: 409 VAL-NEGOCIO. correoEnvio se valida pero el envío es HU-065."
    ),
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
)
def generar_factura(body: FacturaGenerar, servicio: FacturaService = Depends(get_factura_service)):
    factura = servicio.generar(body.model_dump())
    data = FacturaGenerada.model_validate(factura).model_dump(by_alias=True)
    return envelope(success=True, message="Factura de servicio generada correctamente", data=data, status_code=201)
