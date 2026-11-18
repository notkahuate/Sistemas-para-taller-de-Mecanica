"""Casos de uso de repuestos."""
from app.domain.entities.repuesto import CATEGORIAS, ESTADO_ACTIVO, Repuesto
from app.domain.exceptions.errors import FormatoInvalidoError, NoEncontradoError, ReglaNegocioError
from app.domain.interfaces.repuesto_repository import IRepuestoRepository
from app.services.validators.repuesto_validator import validar_formato_repuesto

MSG_DATOS_INVALIDOS = "No fue posible completar «Registrar repuesto»: los datos enviados no son válidos."
MSG_REGLA_NEGOCIO = "No fue posible completar «Registrar repuesto»: la operación viola una regla de negocio."


class RepuestoService:
    def __init__(self, repositorio: IRepuestoRepository):
        self.repositorio = repositorio

    def registrar(self, datos: dict) -> Repuesto:
        """HU-031 Registrar repuesto. El stock arranca en 0; las entradas se registran en HU-037."""
        datos = {
            **datos,
            "referencia": datos["referencia"].strip().upper(),
            "id_categoria": datos["id_categoria"].strip().upper(),
            "id_proveedor": (datos.get("id_proveedor") or "").strip() or None,
            "descripcion": (datos.get("descripcion") or "").strip() or None,
        }
        errores = validar_formato_repuesto(datos)
        if errores:
            campo, detalle = errores[0]
            raise FormatoInvalidoError(MSG_DATOS_INVALIDOS, detalle, campo)

        if datos["id_categoria"] not in CATEGORIAS:
            raise NoEncontradoError(
                f"No existe la categoría {datos['id_categoria']}. Use: {', '.join(CATEGORIAS)}.", "idCategoria"
            )

        if self.repositorio.existe_referencia(datos["referencia"]):
            raise ReglaNegocioError(MSG_REGLA_NEGOCIO, "VAL-NEGOCIO", "Referencia duplicada", "referencia")

        return self.repositorio.crear({**datos, "estado": ESTADO_ACTIVO})
