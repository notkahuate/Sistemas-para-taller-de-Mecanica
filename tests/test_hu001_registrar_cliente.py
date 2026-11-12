"""Casos de prueba de HU-001 Registrar cliente (Parcial #2, FUN-01)."""
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
    "idCliente", "tipoDocumento", "numeroDocumento", "nombreCompleto",
    "telefono", "correo", "direccion", "estado", "fechaRegistro",
}


def test_caso1_registro_exitoso(client):
    r = client.post(URL, json=BODY)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Cliente registrado correctamente"
    assert cuerpo["data"]["idCliente"] == "CLI-0001"
    assert cuerpo["data"]["estado"] == "activo"


def test_caso2_contrato_json(client):
    cuerpo = client.post(URL, json=BODY).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert set(cuerpo["data"]) == CAMPOS_DATA
    assert cuerpo["data"]["fechaRegistro"].endswith("-05:00")


def test_caso3_documento_duplicado_rn12(client):
    client.post(URL, json=BODY)
    r = client.post(URL, json={**BODY, "correo": "otro@email.com"})
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No fue posible registrar el cliente."
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [
        {"campo": "numeroDocumento", "codigo": "RN-12", "detalle": "El documento ya se encuentra registrado."}
    ]


def test_caso4_correo_invalido(client):
    r = client.post(URL, json={**BODY, "correo": "carlos.perez"})
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No fue posible registrar el cliente."
    assert cuerpo["errors"][0] == {"campo": "correo", "codigo": "VAL-FORMATO", "detalle": "Formato de correo no válido."}


def test_telefono_invalido(client):
    r = client.post(URL, json={**BODY, "telefono": "5001234567"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "telefono"


def test_tipo_documento_invalido(client):
    r = client.post(URL, json={**BODY, "tipoDocumento": "TI"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "tipoDocumento"


def test_no_acepta_estado_en_el_body(client):
    r = client.post(URL, json={**BODY, "estado": "inactivo"})
    assert r.status_code == 400
    assert r.json()["success"] is False


def test_id_consecutivo(client):
    client.post(URL, json=BODY)
    r = client.post(URL, json={**BODY, "numeroDocumento": "1098765433"})
    assert r.json()["data"]["idCliente"] == "CLI-0002"


def test_caso5_fallo_de_base_de_datos(client):
    with patch(
        "app.repositories.cliente_repository.ClienteRepository.existe_documento",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = client.post(URL, json=BODY)
    assert r.status_code == 503
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No fue posible completar la operación por indisponibilidad de la base de datos."
    assert cuerpo["errors"][0]["codigo"] == "DB-DOWN"
