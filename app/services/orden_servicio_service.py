"""Casos de uso de órdenes de servicio."""
from app.domain.entities.cliente import ESTADO_ACTIVO
from app.domain.entities.motocicleta import ESTADO_ACTIVA
from app.domain.entities.orden_servicio import ESTADO_RECIBIDA, OrdenServicio
from app.domain.exceptions.errors import AppError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.cliente_repository import IClienteRepository
from app.domain.interfaces.motocicleta_repository import IMotocicletaRepository
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository
from app.services.validators.orden_servicio_validator import validar_formato_orden

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar orden de servicio»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar orden de servicio»: la operación viola una regla de negocio."


class DatosOrdenInvalidosError(AppError):
    status_code = 400


class OrdenServicioService:
    def __init__(
        self,
        repositorio: IOrdenServicioRepository,
        clientes: IClienteRepository,
        motocicletas: IMotocicletaRepository,
    ):
        self.repositorio = repositorio
        self.clientes = clientes
        self.motocicletas = motocicletas

    def registrar(self, datos: dict) -> OrdenServicio:
        """HU-016 Registrar orden de servicio."""
        errores = validar_formato_orden(datos)
        if errores:
            campo, codigo, detalle = errores[0]
            raise DatosOrdenInvalidosError(MSG_DATOS_INVALIDOS, codigo, detalle, campo)

        cliente = self.clientes.obtener_por_id(datos["id_cliente"])
        if cliente is None:
            raise NoEncontradoError("No existe un cliente para el identificador indicado", "idCliente")
        motocicleta = self.motocicletas.obtener_por_id(datos["id_motocicleta"])
        if motocicleta is None:
            raise NoEncontradoError("No existe una motocicleta para el identificador indicado", "idMotocicleta")

        # RN-01: cliente y motocicleta activos, y la moto debe pertenecer al cliente.
        if cliente.estado != ESTADO_ACTIVO or motocicleta.estado != ESTADO_ACTIVA:
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "RN-01", "Cliente o motocicleta inactivos RN-01", "request")
        if motocicleta.id_cliente != cliente.id_cliente:
            raise ReglaNegocioError(
                MSG_REGLA_NEGOCIO, "RN-01", "La motocicleta no pertenece al cliente indicado RN-01", "idMotocicleta"
            )

        # Una moto no puede tener dos órdenes abiertas al mismo tiempo (refinamiento del MVP).
        if self.repositorio.tiene_orden_abierta(motocicleta.id_motocicleta):
            raise ReglaNegocioError(
                MSG_REGLA_NEGOCIO, "ORD-ABIERTA", "La motocicleta ya tiene una orden de servicio abierta", "idMotocicleta"
            )

        datos = {**datos, "motivo_visita": datos["motivo_visita"].strip(), "estado": ESTADO_RECIBIDA, "id_tecnico": None}
        return self.repositorio.crear(datos)
