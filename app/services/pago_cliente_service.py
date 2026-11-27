"""Caso de uso HU-066 Registrar pago de cliente (RN-11)."""
from decimal import Decimal

from app.domain.entities.factura import ESTADO_ANULADA, ID_FACTURA_RE, Factura, aplicar_pago
from app.domain.entities.pago_cliente import METODOS_PAGO, PagoCliente
from app.domain.exceptions.errors import FormatoInvalidoError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.factura_repository import IFacturaRepository
from app.domain.interfaces.pago_cliente_repository import IPagoClienteRepository

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar pago de cliente»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar pago de cliente»: la operación viola una regla de negocio."
MSG_NO_EXISTE = "No fue posible completar «Registrar pago de cliente»: no existe el recurso indicado."


class PagoClienteService:
    def __init__(self, facturas: IFacturaRepository, pagos: IPagoClienteRepository):
        self.facturas = facturas
        self.pagos = pagos

    def _validar_formato(self, datos: dict) -> None:
        def error(campo: str, detalle: str):
            return FormatoInvalidoError(MSG_DATOS_INVALIDOS, detalle, campo)

        if not ID_FACTURA_RE.match(datos["id_factura"]):
            raise error("idFactura", "Formato de idFactura no válido. Debe ser FAC-NNNN.")
        valor: Decimal = datos["valor"]
        if valor <= 0:
            raise error("valor", "El valor debe ser mayor que cero.")
        if valor != valor.quantize(Decimal("0.01")):
            raise error("valor", "El valor admite máximo 2 decimales.")
        if datos["metodo"] not in METODOS_PAGO:
            raise error("metodo", "Método de pago no válido. Use efectivo, transferencia, tarjeta u otros.")
        if not datos["referencia_comprobante"].strip():
            raise error("referenciaComprobante", "La referencia del comprobante es obligatoria.")

    def registrar(self, datos: dict) -> tuple[PagoCliente, Factura]:
        self._validar_formato(datos)

        factura = self.facturas.obtener_por_id(datos["id_factura"])
        if factura is None:
            raise NoEncontradoError("Factura inexistente", "idFactura", MSG_NO_EXISTE)
        if factura.estado == ESTADO_ANULADA:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "VAL-NEGOCIO", "Factura anulada", "request")
        # RN-11: el pago no puede superar el saldo pendiente (una factura pagada tiene saldo 0).
        if datos["valor"] > factura.saldo_pendiente:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-11", "Valor supera saldo pendiente RN-11", "request")

        saldo, estado = aplicar_pago(factura.saldo_pendiente, datos["valor"])
        return self.pagos.registrar(
            {**datos, "referencia_comprobante": datos["referencia_comprobante"].strip()}, saldo, estado
        )
