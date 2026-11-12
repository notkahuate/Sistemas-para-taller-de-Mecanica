"""Casos de prueba de HU-002 Consultar cliente (Parcial #2, FUN-02)."""
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from tests.conftest import CAMPOS_ENVELOPE

URL = "/api/v1/clientes"
BODY = {
    "tipoDocumento": "CC",
    "numeroDocumento": "1098765432",
    "nombreCompleto": "Carlos Andrés Pérez Gómez",
    "telefono": "3001234567",
    "correo": "carlos.perez@email.com",
    "direccion": "Calle 45 # 12-30, Bucaramanga",
}
CAMPOS_DATA = {
    "idCliente", "tipoDocumento", "numeroDocumento", "nombreCompleto", "telefono",
    "correo", "direccion", "estado", "fechaRegistro", "fechaModificacion",
}


def _registrar(client) -> str:
    return client.post(URL, json=BODY).json()["data"]["idCliente"]


def test_caso1_cliente_existente(client):
    id_cliente = _registrar(client)
    r = client.get(f"{URL}/{id_cliente}")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Consulta de cliente exitosa"
    assert cuerpo["data"]["numeroDocumento"] == "1098765432"


def test_caso2_contrato_json(client):
    id_cliente = _registrar(client)
    cuerpo = client.get(f"{URL}/{id_cliente}").json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert set(cuerpo["data"]) == CAMPOS_DATA
    assert cuerpo["data"]["fechaRegistro"].endswith("-05:00")


def test_caso3_formato_de_id_incorrecto(client):
    r = client.get(f"{URL}/1024")
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No fue posible consultar el cliente."
    assert cuerpo["errors"] == [
        {"campo": "idCliente", "codigo": "VAL-FORMATO", "detalle": "Formato de idCliente no válido. Debe ser CLI-NNNN."}
    ]


def test_caso4_cliente_inexistente(client):
    r = client.get(f"{URL}/CLI-9999")
    assert r.status_code == 404
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No existe un cliente para el identificador indicado"
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [
        {"campo": "idCliente", "codigo": "NOT-FOUND", "detalle": "No existe un cliente para el identificador indicado"}
    ]


def test_caso5_fallo_de_base_de_datos(client):
    with patch(
        "app.repositories.cliente_repository.ClienteRepository.obtener_por_id",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = client.get(f"{URL}/CLI-0001")
    assert r.status_code == 503
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["errors"][0]["codigo"] == "DB-DOWN"
