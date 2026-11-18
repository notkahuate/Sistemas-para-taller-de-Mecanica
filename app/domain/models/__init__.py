"""Modelos de base de datos. Importarlos aquí registra sus tablas en Base.metadata."""
from app.domain.models.cliente import ClienteModel  # noqa: F401
from app.domain.models.motocicleta import MotocicletaModel  # noqa: F401
from app.domain.models.orden_servicio import OrdenServicioModel  # noqa: F401
from app.domain.models.usuario import UsuarioModel  # noqa: F401
