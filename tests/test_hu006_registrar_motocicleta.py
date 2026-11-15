"""Casos de prueba de HU-006 Registrar motocicleta (Parcial #2, FUN-06)."""
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from tests.conftest import CAMPOS_ENVELOPE

URL = "/api/v1/motocicletas"
CLIENTE = {
    "tipoDocumento": "CC",
    "numeroDocumento": "1098765432",
    "nombreCompleto": "Carlos Andrés Pérez Gómez",
    "telefono": "3001234567",
    "correo": "carlos.perez@email.com",
    "direccion": "Calle 45 # 12-30, Bucaramanga",
}
MOTO = {
    "placa": "ABC12D",
    "vin": "9BWZZZZ377VT00432",
    "marca": "Yamaha",
    "linea": "FZ 2.0",
    "anio": 2023,
    "cilindraje": 150,
    "color": "Azul",
}
CAMPOS_DATA = {"idMotocicleta", "placa", "vin", "marca", "linea", "anio", "cilindraje", "color", "idCliente", "estado"}
MSG_INVALIDOS = "No fue posible completar «Registrar motocicleta»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar motocicleta»: la operación viola una regla de negocio."


def _cliente(client) -> str:
    return client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]


def test_caso1_registro_exitoso(client):
    id_cliente = _cliente(client)
    r = client.post(URL, json={**MOTO, "idCliente": id_cliente})
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Motocicleta registrada correctamente"
    assert cuerpo["data"] == {**MOTO, "idMotocicleta": "MTO-0001", "idCliente": id_cliente, "estado": "activa"}


def test_caso2_contrato_json(client):
    cuerpo = client.post(URL, json={**MOTO, "idCliente": _cliente(client)}).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert set(cuerpo["data"]) == CAMPOS_DATA


def test_caso3_placa_duplicada_rn12(client):
    id_cliente = _cliente(client)
    client.post(URL, json={**MOTO, "idCliente": id_cliente})
    r = client.post(URL, json={**MOTO, "idCliente": id_cliente, "vin": None})
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "placa", "codigo": "RN-12", "detalle": "Placa duplicada RN-12"}]


def test_caso4_placa_formato_invalido(client):
    r = client.post(URL, json={**MOTO, "placa": "AB-1", "idCliente": _cliente(client)})
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["errors"] == [{"campo": "placa", "codigo": "VAL-FORMATO", "detalle": "Placa con formato inválido"}]


def test_caso5_fallo_de_base_de_datos(client):
    id_cliente = _cliente(client)
    with patch(
        "app.repositories.motocicleta_repository.MotocicletaRepository.existe_placa",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = client.post(URL, json={**MOTO, "idCliente": id_cliente})
    assert r.status_code == 503
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_placa_en_minusculas_se_guarda_en_mayusculas(client):
    r = client.post(URL, json={**MOTO, "placa": "abc12d", "idCliente": _cliente(client)})
    assert r.status_code == 201
    assert r.json()["data"]["placa"] == "ABC12D"


def test_vin_es_opcional(client):
    r = client.post(URL, json={**MOTO, "vin": None, "idCliente": _cliente(client)})
    assert r.status_code == 201
    assert r.json()["data"]["vin"] is None


def test_anio_fuera_de_rango(client):
    r = client.post(URL, json={**MOTO, "anio": 1975, "idCliente": _cliente(client)})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "anio"


def test_cilindraje_fuera_de_rango(client):
    r = client.post(URL, json={**MOTO, "cilindraje": 2000, "idCliente": _cliente(client)})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "cilindraje"


def test_cliente_inexistente_404(client):
    r = client.post(URL, json={**MOTO, "idCliente": "CLI-9999"})
    assert r.status_code == 404
    assert r.json()["errors"][0]["codigo"] == "NOT-FOUND"


def test_cliente_inactivo_rn01(client):
    from app.core.database import SessionLocal
    from app.domain.models.cliente import ClienteModel

    id_cliente = _cliente(client)
    with SessionLocal() as db:
        db.query(ClienteModel).filter_by(id_cliente=id_cliente).update({"estado": "inactivo"})
        db.commit()
    r = client.post(URL, json={**MOTO, "idCliente": id_cliente})
    assert r.status_code == 409
    assert r.json()["errors"][0]["codigo"] == "RN-01"


def test_requiere_token(client_sin_token):
    assert client_sin_token.post(URL, json={**MOTO, "idCliente": "CLI-0001"}).status_code == 401
