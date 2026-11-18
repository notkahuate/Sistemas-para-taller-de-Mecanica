"""Casos de uso de motocicletas."""
from app.domain.entities.cliente import ESTADO_ACTIVO
from app.domain.entities.motocicleta import (
    ESTADO_ACTIVA,
    ID_MOTOCICLETA_RE,
    Motocicleta,
    normalizar_placa,
    validar_placa_consulta,
)
from app.domain.exceptions.errors import FormatoInvalidoError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.cliente_repository import IClienteRepository
from app.domain.interfaces.motocicleta_repository import IMotocicletaRepository
from app.services.validators.motocicleta_validator import validar_formato_motocicleta

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar motocicleta»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar motocicleta»: la operación viola una regla de negocio."
MSG_CONSULTA_INVALIDA = "No fue posible completar «Consultar motocicleta»: los datos enviados no son válidos."
MSG_CONSULTA_NO_EXISTE = "No fue posible completar «Consultar motocicleta»: no existe el recurso indicado."


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

    def consultar_por_id(self, id_motocicleta: str) -> tuple[Motocicleta, str | None]:
        """HU-007 Consultar motocicleta por idMotocicleta. Devuelve la motocicleta y el nombre del propietario."""
        if not ID_MOTOCICLETA_RE.match(id_motocicleta):
            raise FormatoInvalidoError(
                MSG_CONSULTA_INVALIDA, "Formato de idMotocicleta no válido. Debe ser MTO-NNNN.", "idMotocicleta"
            )
        motocicleta = self.repositorio.obtener_por_id(id_motocicleta)
        if motocicleta is None:
            raise NoEncontradoError("No existe", "idMotocicleta", MSG_CONSULTA_NO_EXISTE)
        return motocicleta, self._nombre_propietario(motocicleta)

    def consultar_por_placa(self, placa: str | None) -> tuple[Motocicleta, str | None]:
        """HU-007 Consultar motocicleta por placa. La placa se normaliza a mayúsculas (RN-12: placa única)."""
        placa = normalizar_placa(placa or "")
        detalle = validar_placa_consulta(placa)
        if detalle:
            raise FormatoInvalidoError(MSG_CONSULTA_INVALIDA, detalle, "placa")
        motocicleta = self.repositorio.obtener_por_placa(placa)
        if motocicleta is None:
            raise NoEncontradoError("No existe", "placa", MSG_CONSULTA_NO_EXISTE)
        return motocicleta, self._nombre_propietario(motocicleta)

    def _nombre_propietario(self, motocicleta: Motocicleta) -> str | None:
        """El propietario lo entrega el módulo de clientes, a través de su repositorio."""
        cliente = self.clientes.obtener_por_id(motocicleta.id_cliente)
        return cliente.nombre_completo if cliente else None
