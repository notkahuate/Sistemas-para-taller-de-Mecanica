"""Casos de prueba de HU-076 Registrar técnico (Parcial #2, FUN-76)."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from tests.conftest import CAMPOS_ENVELOPE, iniciar_sesion

URL = "/api/v1/tecnicos"
BODY = {
    "tipoDocumento": "CC",
    "numeroDocumento": "109111222",
    "nombreCompleto": "Luis Martínez",
    "telefono": "3002223344",
    "correo": "luis.martinez@motoservice.com",
    "cargo": "Técnico de frenos",
    "fechaIngreso": "2026-02-01",
    "tarifaHoraria": 40000.0,
}
CAMPOS_DATA = {"idTecnico", "numeroDocumento", "nombreCompleto", "estado", "tarifaHoraria", "fechaIngreso"}
MSG_INVALIDOS = "No fue posible completar «Registrar técnico»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar técnico»: la operación viola una regla de negocio."


@pytest.fixture
def admin(client_sin_token):
    """Registrar técnicos es una función del administrador del taller."""
    client_sin_token.headers["Authorization"] = f"Bearer {iniciar_sesion(client_sin_token, 'admin', 'Admin123*')}"
    return client_sin_token


def test_caso1_registro_exitoso(admin):
    r = admin.post(URL, json=BODY)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Técnico registrado correctamente"
    assert cuerpo["data"] == {
        "idTecnico": "TEC-0001",
        "numeroDocumento": "109111222",
        "nombreCompleto": "Luis Martínez",
        "estado": "activo",
        "tarifaHoraria": 40000.0,
        "fechaIngreso": "2026-02-01",
    }


def test_caso2_contrato_json(admin):
    cuerpo = admin.post(URL, json=BODY).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert set(cuerpo["data"]) == CAMPOS_DATA


def test_caso3_documento_duplicado(admin):
    admin.post(URL, json=BODY)
    r = admin.post(URL, json={**BODY, "correo": "otro@motoservice.com"})
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "VAL-NEGOCIO", "detalle": "Documento duplicado"}]


def test_caso4_fecha_ingreso_futura(admin):
    manana = (date.today() + timedelta(days=2)).isoformat()
    r = admin.post(URL, json={**BODY, "fechaIngreso": manana})
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["errors"] == [{"campo": "fecha", "codigo": "VAL-FORMATO", "detalle": "FechaIngreso futura"}]


def test_caso5_fallo_de_base_de_datos(admin):
    with patch(
        "app.repositories.tecnico_repository.TecnicoRepository.existe_documento",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = admin.post(URL, json=BODY)
    assert r.status_code == 503
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_tarifa_negativa(admin):
    r = admin.post(URL, json={**BODY, "tarifaHoraria": -1})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "tarifaHoraria"


def test_tarifa_cero_es_valida(admin):
    r = admin.post(URL, json={**BODY, "tarifaHoraria": 0})
    assert r.status_code == 201
    assert r.json()["data"]["tarifaHoraria"] == 0.0


def test_tarifa_con_decimales(admin):
    r = admin.post(URL, json={**BODY, "tarifaHoraria": 35500.5})
    assert r.json()["data"]["tarifaHoraria"] == 35500.5


def test_fecha_con_formato_incorrecto(admin):
    r = admin.post(URL, json={**BODY, "fechaIngreso": "01/02/2026"})
    assert r.status_code == 400


def test_correo_invalido(admin):
    r = admin.post(URL, json={**BODY, "correo": "luis.martinez"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "correo"


def test_cargo_obligatorio(admin):
    r = admin.post(URL, json={**BODY, "cargo": "  "})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "cargo"


def test_id_consecutivo(admin):
    admin.post(URL, json=BODY)
    r = admin.post(URL, json={**BODY, "numeroDocumento": "109111223"})
    assert r.json()["data"]["idTecnico"] == "TEC-0002"


def test_recepcion_no_puede_registrar_tecnicos(client):
    assert client.post(URL, json=BODY).status_code == 403


def test_requiere_token(client_sin_token):
    assert client_sin_token.post(URL, json=BODY).status_code == 401
