"""Contratos JSON de órdenes de servicio (camelCase, como en el Parcial #2)."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.responses import a_iso_bogota


class OrdenServicioCrear(BaseModel):
    """Body de POST /api/v1/ordenes-servicio. El estado, el idOrden y el idTecnico los pone el sistema."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "idCliente": "CLI-0001",
                "idMotocicleta": "MTO-0001",
                "motivoVisita": "Mantenimiento 5000 km y ruido en frenos",
                "fechaIngreso": "2026-10-14T08:30:00-05:00",
                "observaciones": "Cliente deja casco en recepción",
                "idCita": None,
            }
        },
    )

    id_cliente: str = Field(alias="idCliente")
    id_motocicleta: str = Field(alias="idMotocicleta")
    motivo_visita: str = Field(alias="motivoVisita", max_length=300)
    fecha_ingreso: datetime = Field(alias="fechaIngreso")
    observaciones: str | None = Field(default=None, max_length=500)
    id_cita: str | None = Field(default=None, alias="idCita")


class OrdenServicioRegistrada(BaseModel):
    """data de la respuesta de HU-016."""

    model_config = ConfigDict(from_attributes=True)

    id_orden: str = Field(serialization_alias="idOrden")
    id_cliente: str = Field(serialization_alias="idCliente")
    id_motocicleta: str = Field(serialization_alias="idMotocicleta")
    id_cita: str | None = Field(serialization_alias="idCita")
    motivo_visita: str = Field(serialization_alias="motivoVisita")
    estado: str
    fecha_ingreso: datetime = Field(serialization_alias="fechaIngreso")
    observaciones: str | None
    id_tecnico: str | None = Field(serialization_alias="idTecnico")

    @field_serializer("fecha_ingreso")
    def _fecha_iso(self, valor: datetime) -> str:
        return a_iso_bogota(valor)


class TecnicoAsignar(BaseModel):
    """Body de PATCH /api/v1/ordenes-servicio/{idOrden}/tecnico (HU-017)."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "idTecnico": "TEC-0001",
                "idEspecialidadRequerida": "ESP-FRE",
                "fechaAsignacion": "2026-10-14T09:00:00-05:00",
            }
        },
    )

    id_tecnico: str = Field(alias="idTecnico")
    id_especialidad_requerida: str | None = Field(default=None, alias="idEspecialidadRequerida")
    fecha_asignacion: datetime = Field(alias="fechaAsignacion")


class AsignacionTecnico(BaseModel):
    """data de la respuesta de HU-017."""

    id_orden: str = Field(serialization_alias="idOrden")
    id_tecnico: str = Field(serialization_alias="idTecnico")
    nombre_tecnico: str = Field(serialization_alias="nombreTecnico")
    id_especialidad_requerida: str | None = Field(serialization_alias="idEspecialidadRequerida")
    estado: str
    fecha_asignacion: datetime = Field(serialization_alias="fechaAsignacion")

    @field_serializer("fecha_asignacion")
    def _fecha_iso(self, valor: datetime) -> str:
        return a_iso_bogota(valor)


class EstadoOrden(BaseModel):
    """data de la respuesta de HU-018 Consultar estado de la orden."""

    id_orden: str = Field(serialization_alias="idOrden")
    id_cliente: str = Field(serialization_alias="idCliente")
    id_motocicleta: str = Field(serialization_alias="idMotocicleta")
    placa: str | None
    estado: str
    id_tecnico: str | None = Field(serialization_alias="idTecnico")
    motivo_visita: str = Field(serialization_alias="motivoVisita")
    fecha_ingreso: datetime = Field(serialization_alias="fechaIngreso")
    fecha_cierre: datetime | None = Field(serialization_alias="fechaCierre")
    tiene_diagnostico: bool = Field(serialization_alias="tieneDiagnostico")
    actividades_registradas: int = Field(serialization_alias="actividadesRegistradas")
    repuestos_consumidos: int = Field(serialization_alias="repuestosConsumidos")

    @field_serializer("fecha_ingreso")
    def _fecha_ingreso(self, valor: datetime) -> str:
        return a_iso_bogota(valor)

    @field_serializer("fecha_cierre")
    def _fecha_cierre(self, valor: datetime | None) -> str | None:
        return a_iso_bogota(valor) if valor else None


class OrdenCerrar(BaseModel):
    """Body de POST /api/v1/ordenes-servicio/{idOrden}/cerrar (HU-020)."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={"example": {"confirmarCierre": True, "notificarCliente": True}},
    )

    confirmar_cierre: bool = Field(alias="confirmarCierre", strict=True)
    notificar_cliente: bool = Field(alias="notificarCliente", strict=True)


def _dinero(valor: Decimal) -> float:
    return float(valor.quantize(Decimal("0.01")))


class TotalesCierre(BaseModel):
    mano_obra: Decimal = Field(serialization_alias="manoObra")
    repuestos: Decimal
    subtotal: Decimal
    impuestos: Decimal
    descuentos: Decimal
    total: Decimal

    @field_serializer("mano_obra", "repuestos", "subtotal", "impuestos", "descuentos", "total")
    def _montos(self, valor: Decimal) -> float:
        return _dinero(valor)


class OrdenCerrada(BaseModel):
    """data de la respuesta de HU-020."""

    id_orden: str = Field(serialization_alias="idOrden")
    estado: str
    fecha_cierre: datetime = Field(serialization_alias="fechaCierre")
    totales: TotalesCierre
    id_factura: str = Field(serialization_alias="idFactura")
    notificacion_cliente: str = Field(serialization_alias="notificacionCliente")

    @field_serializer("fecha_cierre")
    def _fecha(self, valor: datetime) -> str:
        return a_iso_bogota(valor)
