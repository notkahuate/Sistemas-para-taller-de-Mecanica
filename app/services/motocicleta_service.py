"""Casos de uso de motocicletas."""
from app.domain.entities.cliente import ESTADO_ACTIVO
from app.domain.entities.motocicleta import ESTADO_ACTIVA, Motocicleta
from app.domain.exceptions.errors import FormatoInvalidoError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.cliente_repository import IClienteRepository
from app.domain.interfaces.motocicleta_repository import IMotocicletaRepository
from app.services.validators.motocicleta_validator import validar_formato_motocicleta

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar motocicleta»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar motocicleta»: la operación viola una regla de negocio."


class MotocicletaService:
    def __init__(self, repositorio: IMotocicletaRepository, clientes: IClienteRepository):
        self.repositorio = repositorio
        self.clientes = clientes

    def registrar(self, datos: dict) -> Motocicleta:
        """HU-006 Registrar motocicleta."""
        datos = {**datos, "placa": datos["placa"].strip().upper()}
        if datos.get("vin"):
            datos["vin"] = datos["vin"].strip().upper()

        errores = validar_formato_motocicleta(datos)
        if errores:
            campo, detalle = errores[0]
            raise FormatoInvalidoError(MSG_DATOS_INVALIDOS, detalle, campo)

        # RN-01: el propietario debe existir y estar activo.
        cliente = self.clientes.obtener_por_id(datos["id_cliente"])
        if cliente is None:
            raise NoEncontradoError("No existe un cliente para el identificador indicado", "idCliente")
        if cliente.estado != ESTADO_ACTIVO:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-01", "El cliente propietario no está activo RN-01", "idCliente")

        # RN-12: la placa no se puede repetir.
        if self.repositorio.existe_placa(datos["placa"]):
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-12", "Placa duplicada RN-12", "placa")

        return self.repositorio.crear({**datos, "estado": ESTADO_ACTIVA})
