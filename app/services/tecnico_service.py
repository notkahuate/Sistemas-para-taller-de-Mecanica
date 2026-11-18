"""Casos de uso de técnicos."""
from datetime import date

from app.core.responses import ahora_bogota
from app.domain.entities.tecnico import ESTADO_ACTIVO, Tecnico
from app.domain.exceptions.errors import FormatoInvalidoError, ReglaNegocioError
from app.domain.interfaces.tecnico_repository import ITecnicoRepository
from app.services.validators.tecnico_validator import validar_formato_tecnico

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar técnico»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar técnico»: la operación viola una regla de negocio."


class TecnicoService:
    def __init__(self, repositorio: ITecnicoRepository):
        self.repositorio = repositorio

    def registrar(self, datos: dict, hoy: date | None = None) -> Tecnico:
        """HU-076 Registrar técnico."""
        hoy = hoy or ahora_bogota().date()
        errores = validar_formato_tecnico(datos, hoy)
        if errores:
            campo, detalle = errores[0]
            raise FormatoInvalidoError(MSG_DATOS_INVALIDOS, detalle, campo)

        # El número de documento del técnico no se puede repetir.
        if self.repositorio.existe_documento(datos["numero_documento"]):
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "VAL-NEGOCIO", "Documento duplicado", "request")

        return self.repositorio.crear({**datos, "estado": ESTADO_ACTIVO})
