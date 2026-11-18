"""Casos de uso de órdenes de servicio."""
from app.domain.entities.cliente import ESTADO_ACTIVO
from app.domain.entities.motocicleta import ESTADO_ACTIVA
from app.domain.entities.orden_servicio import ESTADO_EN_PROCESO, ESTADO_FINALIZADA, ESTADO_RECIBIDA, OrdenServicio
from app.domain.entities.tecnico import ESTADO_ACTIVO as TECNICO_ACTIVO
from app.domain.entities.tecnico import Tecnico
from app.domain.exceptions.errors import AppError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.cliente_repository import IClienteRepository
from app.domain.interfaces.motocicleta_repository import IMotocicletaRepository
from app.domain.interfaces.orden_servicio_repository import IOrdenServicioRepository
from app.domain.interfaces.tecnico_repository import ITecnicoRepository
from app.services.validators.orden_servicio_validator import validar_formato_asignacion, validar_formato_orden

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar orden de servicio»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar orden de servicio»: la operación viola una regla de negocio."
MSG_ASIGNAR_DATOS_INVALIDOS = "No fue posible completar «Asignar técnico a la orden»: los datos enviados no son válidos."
MSG_ASIGNAR_REGLA_NEGOCIO = "No fue posible completar «Asignar técnico a la orden»: la operación viola una regla de negocio."


class DatosOrdenInvalidosError(AppError):
    status_code = 400


class OrdenServicioService:
    def __init__(
        self,
        repositorio: IOrdenServicioRepository,
        clientes: IClienteRepository,
        motocicletas: IMotocicletaRepository,
        tecnicos: ITecnicoRepository,
    ):
        self.repositorio = repositorio
        self.clientes = clientes
        self.motocicletas = motocicletas
        self.tecnicos = tecnicos

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

    def asignar_tecnico(self, id_orden: str, datos: dict) -> tuple[OrdenServicio, Tecnico]:
        """HU-017 Asignar técnico a la orden (gemela de HU-089)."""
        errores = validar_formato_asignacion(id_orden, datos)
        if errores:
            campo, codigo, detalle = errores[0]
            raise DatosOrdenInvalidosError(MSG_ASIGNAR_DATOS_INVALIDOS, codigo, detalle, campo)

        orden = self.repositorio.obtener_por_id(id_orden)
        if orden is None:
            raise NoEncontradoError("No existe una orden de servicio para el identificador indicado", "idOrden")
        tecnico = self.tecnicos.obtener_por_id(datos["id_tecnico"])
        if tecnico is None:
            raise NoEncontradoError("No existe un técnico para el identificador indicado", "idTecnico")

        # RN-02: una orden finalizada ya no admite cambios.
        if orden.estado == ESTADO_FINALIZADA:
            raise ReglaNegocioError(MSG_ASIGNAR_REGLA_NEGOCIO, "RN-02", "Orden finalizada RN-02", "request")
        # RN-06 (alcance MVP): el técnico debe estar activo. Especialidad y disponibilidad quedan para v2
        # porque dependen de HU-084 y HU-086, que no entran en el MVP.
        if tecnico.estado != TECNICO_ACTIVO:
            raise ReglaNegocioError(MSG_ASIGNAR_REGLA_NEGOCIO, "RN-06", "Técnico inactivo RN-06", "request")

        cambios = {
            "id_tecnico": tecnico.id_tecnico,
            "id_especialidad_requerida": datos.get("id_especialidad_requerida"),
            "fecha_asignacion": datos["fecha_asignacion"],
            "estado": ESTADO_EN_PROCESO,
        }
        return self.repositorio.asignar_tecnico(id_orden, cambios), tecnico
