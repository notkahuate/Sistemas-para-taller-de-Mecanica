"""Casos de prueba de HU-031 Registrar repuesto (Parcial #2, FUN-31)."""
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from tests.conftest import CAMPOS_ENVELOPE, iniciar_sesion

URL = "/api/v1/repuestos"
BODY = {
    "referencia": "PAS-FZ150",
    "nombre": "Pastillas freno delantero FZ 150",
    "descripcion": "Juego original",
    "idCategoria": "CAT-FRE",
    "idProveedor": "PRV-08",
    "costo": 28000.0,
    "precio": 45000.0,
    "stockMinimo": 2,
}
CAMPOS_DATA = {"idRepuesto", "referencia", "estado", "stockDisponible", "costo", "precio"}
MSG_INVALIDOS = "No fue posible completar «Registrar repuesto»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar repuesto»: la operación viola una regla de negocio."


@pytest.fixture
def inventario(client_sin_token):
    """Registrar repuestos es una función del encargado de inventario."""
    client_sin_token.headers["Authorization"] = f"Bearer {iniciar_sesion(client_sin_token, 'inventario', 'Inventario123*')}"
    return client_sin_token


def test_caso1_registro_exitoso(inventario):
    r = inventario.post(URL, json=BODY)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Repuesto registrado correctamente"
    assert cuerpo["data"] == {
        "idRepuesto": "REP-0001",
        "referencia": "PAS-FZ150",
        "estado": "activo",
        "stockDisponible": 0,
        "costo": 28000.0,
        "precio": 45000.0,
    }


def test_caso2_contrato_json(inventario):
    cuerpo = inventario.post(URL, json=BODY).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert set(cuerpo["data"]) == CAMPOS_DATA


def test_caso3_referencia_duplicada(inventario):
    inventario.post(URL, json=BODY)
    r = inventario.post(URL, json={**BODY, "referencia": "pas-fz150", "nombre": "Otro"})
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "referencia", "codigo": "VAL-NEGOCIO", "detalle": "Referencia duplicada"}]


def test_caso4_precio_menor_que_costo(inventario):
    r = inventario.post(URL, json={**BODY, "precio": 20000.0})
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "VAL-FORMATO", "detalle": "Precio menor que costo"}]


def test_caso5_fallo_de_base_de_datos(inventario):
    with patch(
        "app.repositories.repuesto_repository.RepuestoRepository.existe_referencia",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = inventario.post(URL, json=BODY)
    assert r.status_code == 503
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_precio_igual_al_costo_es_valido(inventario):
    r = inventario.post(URL, json={**BODY, "precio": 28000.0})
    assert r.status_code == 201


def test_costo_negativo(inventario):
    r = inventario.post(URL, json={**BODY, "costo": -1})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "costo"


def test_referencia_muy_corta(inventario):
    r = inventario.post(URL, json={**BODY, "referencia": "AB"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "referencia"


def test_categoria_inexistente(inventario):
    r = inventario.post(URL, json={**BODY, "idCategoria": "CAT-XXX"})
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "idCategoria"


def test_proveedor_y_descripcion_opcionales(inventario):
    body = {k: v for k, v in BODY.items() if k not in ("idProveedor", "descripcion")}
    r = inventario.post(URL, json=body)
    assert r.status_code == 201


def test_stock_minimo_negativo(inventario):
    r = inventario.post(URL, json={**BODY, "stockMinimo": -1})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "stockMinimo"


def test_referencia_se_guarda_en_mayusculas(inventario):
    r = inventario.post(URL, json={**BODY, "referencia": "pas-fz150"})
    assert r.json()["data"]["referencia"] == "PAS-FZ150"


def test_administrador_tambien_puede_registrar(client_sin_token):
    token = iniciar_sesion(client_sin_token, "admin", "Admin123*")
    r = client_sin_token.post(URL, json=BODY, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201


def test_recepcion_no_puede_registrar(client):
    assert client.post(URL, json=BODY).status_code == 403


def test_requiere_token(client_sin_token):
    assert client_sin_token.post(URL, json=BODY).status_code == 401
