"""Casos de prueba de HU-007 Consultar motocicleta (Parcial #2, FUN-07)."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.domain.entities.motocicleta import normalizar_placa, validar_placa_consulta
from main import app
from tests.conftest import CAMPOS_ENVELOPE, iniciar_sesion

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
CAMPOS_DATA = {
    "idMotocicleta", "placa", "vin", "marca", "linea", "anio", "cilindraje",
    "color", "idCliente", "nombrePropietario", "estado",
}
MSG_EXITO = "Consulta de motocicleta exitosa"
MSG_INVALIDOS = "No fue posible completar «Consultar motocicleta»: los datos enviados no son válidos."
MSG_NO_EXISTE = "No fue posible completar «Consultar motocicleta»: no existe el recurso indicado."


def _registrar(client) -> tuple[str, str]:
    """Registra un cliente y su motocicleta (HU-001 + HU-006). Devuelve (idCliente, idMotocicleta)."""
    id_cliente = client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]
    id_moto = client.post(URL, json={**MOTO, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    return id_cliente, id_moto


# ---------- Casos del Parcial ----------

def test_caso1_consulta_exitosa(client):
    id_cliente, id_moto = _registrar(client)
    r = client.get(f"{URL}/{id_moto}")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == MSG_EXITO
    assert cuerpo["data"] == {
        "idMotocicleta": id_moto,
        "placa": "ABC12D",
        "vin": "9BWZZZZ377VT00432",
        "marca": "Yamaha",
        "linea": "FZ 2.0",
        "anio": 2023,
        "cilindraje": 150,
        "color": "Azul",
        "idCliente": id_cliente,
        "nombrePropietario": "Carlos Andrés Pérez Gómez",
        "estado": "activa",
    }


def test_caso2_contrato_json(client):
    _, id_moto = _registrar(client)
    cuerpo = client.get(f"{URL}/{id_moto}").json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert isinstance(cuerpo["success"], bool)
    assert isinstance(cuerpo["message"], str)
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str) and cuerpo["traceId"]
    assert set(cuerpo["data"]) == CAMPOS_DATA
    assert isinstance(cuerpo["data"]["anio"], int)
    assert isinstance(cuerpo["data"]["cilindraje"], int)


def test_caso3_no_existe(client):
    r = client.get(f"{URL}/MTO-9999")
    assert r.status_code == 404
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_NO_EXISTE
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "idMotocicleta", "codigo": "NOT-FOUND", "detalle": "No existe"}]


def test_caso4_placa_con_caracteres_especiales(client):
    _registrar(client)
    r = client.get(URL, params={"placa": "ABC-12"})
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [
        {"campo": "placa", "codigo": "VAL-FORMATO", "detalle": "Placa con caracteres especiales"}
    ]


def test_caso5_fallo_de_base_de_datos(client):
    with patch(
        "app.repositories.motocicleta_repository.MotocicletaRepository.obtener_por_id",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = client.get(f"{URL}/MTO-0001")
    assert r.status_code == 503
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No fue posible completar la operación por indisponibilidad de la base de datos."
    assert cuerpo["errors"] == [{"campo": "persistencia", "codigo": "DB-DOWN", "detalle": "Base de datos no disponible"}]


# ---------- Consulta por placa (GET /api/v1/motocicletas?placa=) ----------

def test_consulta_por_placa_exitosa(client):
    id_cliente, id_moto = _registrar(client)
    r = client.get(URL, params={"placa": "ABC12D"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_EXITO
    assert cuerpo["data"]["idMotocicleta"] == id_moto
    assert cuerpo["data"]["idCliente"] == id_cliente
    assert cuerpo["data"]["nombrePropietario"] == "Carlos Andrés Pérez Gómez"


def test_placa_se_normaliza_a_mayusculas(client):
    _, id_moto = _registrar(client)
    r = client.get(URL, params={"placa": "  abc12d "})
    assert r.status_code == 200
    assert r.json()["data"]["idMotocicleta"] == id_moto


def test_placa_no_registrada(client):
    r = client.get(URL, params={"placa": "ZZZ99Z"})
    assert r.status_code == 404
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_NO_EXISTE
    assert cuerpo["errors"] == [{"campo": "placa", "codigo": "NOT-FOUND", "detalle": "No existe"}]


def test_placa_ausente(client):
    r = client.get(URL)
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["errors"] == [{"campo": "placa", "codigo": "VAL-FORMATO", "detalle": "La placa es obligatoria."}]


def test_placa_con_longitud_invalida(client):
    r = client.get(URL, params={"placa": "AB1"})
    assert r.status_code == 400
    assert r.json()["errors"][0] == {"campo": "placa", "codigo": "VAL-FORMATO", "detalle": "Placa con formato inválido"}


def test_formato_de_id_incorrecto(client):
    r = client.get(f"{URL}/301")
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["errors"] == [
        {"campo": "idMotocicleta", "codigo": "VAL-FORMATO", "detalle": "Formato de idMotocicleta no válido. Debe ser MTO-NNNN."}
    ]


def test_fallo_de_base_de_datos_por_placa(client):
    with patch(
        "app.repositories.motocicleta_repository.MotocicletaRepository.obtener_por_placa",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = client.get(URL, params={"placa": "ABC12D"})
    assert r.status_code == 503
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


# ---------- Token y rol ----------

def test_sin_token(client_sin_token):
    r = client_sin_token.get(f"{URL}/MTO-0001")
    assert r.status_code == 401
    assert r.json()["message"] == "No autorizado."
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"


def test_sin_token_por_placa(client_sin_token):
    r = client_sin_token.get(URL, params={"placa": "ABC12D"})
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"


@pytest.mark.parametrize("usuario,clave", [("tecnico", "Tecnico123*"), ("inventario", "Inventario123*")])
def test_rol_no_autorizado(usuario, clave):
    with TestClient(app) as c:
        c.headers["Authorization"] = f"Bearer {iniciar_sesion(c, usuario, clave)}"
        r = c.get(f"{URL}/MTO-0001")
    assert r.status_code == 403
    assert r.json()["errors"][0]["codigo"] == "AUTH-403"


def test_administrador_puede_consultar(client):
    _, id_moto = _registrar(client)
    with TestClient(app) as c:
        c.headers["Authorization"] = f"Bearer {iniciar_sesion(c, 'admin', 'Admin123*')}"
        r = c.get(f"{URL}/{id_moto}")
    assert r.status_code == 200


# ---------- Domain: RN-12 (la placa es única, se compara normalizada) ----------

@pytest.mark.parametrize("entrada,esperada", [("abc12d", "ABC12D"), ("  ABC12D  ", "ABC12D"), ("AbC12d", "ABC12D")])
def test_domain_rn12_normalizar_placa(entrada, esperada):
    assert normalizar_placa(entrada) == esperada


@pytest.mark.parametrize(
    "placa,detalle",
    [
        ("ABC12D", None),
        ("ABC123", None),
        ("ABC-12", "Placa con caracteres especiales"),
        ("AB C12", "Placa con caracteres especiales"),
        ("ABC#2D", "Placa con caracteres especiales"),
        ("AB1", "Placa con formato inválido"),
        ("ABCDEFG", "Placa con formato inválido"),
        ("", "La placa es obligatoria."),
    ],
)
def test_domain_validar_placa_consulta(placa, detalle):
    assert validar_placa_consulta(placa) == detalle


def test_domain_rn12_misma_placa_en_minusculas_es_la_misma_moto(client):
    """RN-12: como la placa es única, una placa escrita distinto no puede registrarse de nuevo."""
    id_cliente, _ = _registrar(client)
    r = client.post(URL, json={**MOTO, "placa": "abc12d", "idCliente": id_cliente})
    assert r.status_code == 409
    assert r.json()["errors"][0]["codigo"] == "RN-12"
