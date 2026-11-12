"""Casos de uso de clientes."""
from app.core.responses import ahora_bogota
from app.domain.entities.cliente import ESTADO_ACTIVO, Cliente
from app.domain.exceptions.errors import FormatoInvalidoError, ReglaNegocioError
from app.domain.interfaces.cliente_repository import IClienteRepository
from app.services.validators.cliente_validator import validar_formato_cliente

MSG_REGISTRO_FALLIDO = "No fue posible registrar el cliente."


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
