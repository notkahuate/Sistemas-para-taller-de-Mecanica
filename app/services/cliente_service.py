"""Casos de uso de clientes."""
from app.core.responses import ahora_bogota
from app.domain.entities.cliente import ESTADO_ACTIVO, ID_CLIENTE_RE, Cliente
from app.domain.exceptions.errors import FormatoInvalidoError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.cliente_repository import IClienteRepository
from app.services.validators.cliente_validator import validar_formato_cliente

MSG_REGISTRO_FALLIDO = "No fue posible registrar el cliente."
MSG_CONSULTA_FALLIDA = "No fue posible consultar el cliente."
MSG_NO_EXISTE = "No existe un cliente para el identificador indicado"


class ClienteService:
    def __init__(self, repositorio: IClienteRepository):
        self.repositorio = repositorio

    def registrar(self, datos: dict) -> Cliente:
        """HU-001 Registrar cliente."""
        errores = validar_formato_cliente(datos)
        if errores:
            campo, detalle = errores[0]
            raise FormatoInvalidoError(MSG_REGISTRO_FALLIDO, detalle, campo)

        # RN-12: el número de documento no se puede repetir.
        if self.repositorio.existe_documento(datos["numero_documento"]):
            raise ReglaNegocioError(
                MSG_REGISTRO_FALLIDO, "RN-12", "El documento ya se encuentra registrado.", "numeroDocumento"
            )

        nuevo = {**datos, "estado": ESTADO_ACTIVO, "fecha_registro": ahora_bogota()}
        return self.repositorio.crear(nuevo)

    def consultar(self, id_cliente: str) -> Cliente:
        """HU-002 Consultar cliente. Un cliente inactivo también se puede consultar."""
        if not ID_CLIENTE_RE.match(id_cliente):
            raise FormatoInvalidoError(
                MSG_CONSULTA_FALLIDA, "Formato de idCliente no válido. Debe ser CLI-NNNN.", "idCliente"
            )

        cliente = self.repositorio.obtener_por_id(id_cliente)
        if cliente is None:
            raise NoEncontradoError(MSG_NO_EXISTE, "idCliente")
        return cliente
