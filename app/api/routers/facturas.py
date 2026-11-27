"""Endpoints de facturación (MOD-05, SUB-13). Solo reciben la petición, llaman al servicio y responden."""
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import requiere_rol
from app.api.dependencies.facturas import get_factura_service
from app.api.schemas.factura import DetalleFactura, FacturaConsultada, FacturaGenerada, FacturaGenerar
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


@router.get(
    "/{idFactura}",
    summary="HU-062 Consultar factura",
    description=(
        "Devuelve encabezado, estado, total, saldo pendiente, pagos y el detalle de lo cobrado: actividades con su "
        "mano de obra (HU-030) y repuestos consumidos (HU-027). idFactura mal formado: 400; inexistente: 404."
    ),
    dependencies=[Depends(requiere_rol(ROL_RECEPCION, ROL_ADMINISTRADOR))],
)
def consultar_factura(
    idFactura: str,  # noqa: N803  (el contrato usa camelCase en la ruta)
    servicio: FacturaService = Depends(get_factura_service),
):
    r = servicio.consultar(idFactura)
    f = r["factura"]
    data = FacturaConsultada(
        id_factura=f.id_factura,
        id_orden=f.id_orden,
        id_cliente=f.id_cliente,
        estado=f.estado,
        total=f.total,
        saldo_pendiente=f.saldo_pendiente,
        pagos=r["pagos"],
        detalle=DetalleFactura(mano_obra=r["mano_obra"], repuestos=r["repuestos"]),
    ).model_dump(by_alias=True)
    return envelope(success=True, message="Consulta de factura exitosa", data=data)
