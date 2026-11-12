"""Repositorio de clientes: único lugar que lee y escribe la tabla clientes."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.cliente import Cliente, generar_id_cliente
from app.domain.interfaces.cliente_repository import IClienteRepository
from app.domain.models.cliente import ClienteModel


def a_entidad(m: ClienteModel) -> Cliente:
    return Cliente(
        id_cliente=m.id_cliente or "",
        tipo_documento=m.tipo_documento,
        numero_documento=m.numero_documento,
        nombre_completo=m.nombre_completo,
        telefono=m.telefono,
        correo=m.correo,
        direccion=m.direccion,
        estado=m.estado,
        fecha_registro=m.fecha_registro,
        fecha_modificacion=m.fecha_modificacion,
    )


class ClienteRepository(IClienteRepository):
    def __init__(self, db: Session):
        self.db = db

    def existe_documento(self, numero_documento: str) -> bool:
        consulta = select(ClienteModel.secuencia).where(ClienteModel.numero_documento == numero_documento)
        return self.db.scalar(consulta) is not None

    def crear(self, datos: dict) -> Cliente:
        modelo = ClienteModel(**datos)
        self.db.add(modelo)
        try:
            self.db.flush()  # obtiene la secuencia para armar el idCliente
            modelo.id_cliente = generar_id_cliente(modelo.secuencia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return a_entidad(modelo)

    def obtener_por_id(self, id_cliente: str) -> Cliente | None:
        modelo = self.db.scalar(select(ClienteModel).where(ClienteModel.id_cliente == id_cliente))
        return a_entidad(modelo) if modelo else None
