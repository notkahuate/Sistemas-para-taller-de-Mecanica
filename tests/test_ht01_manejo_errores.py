"""Pruebas de HT-01: todas las respuestas de error usan el envelope estándar."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from tests.conftest import CAMPOS_ENVELOPE


def test_error_inesperado_responde_500_con_envelope():
    with TestClient(app, raise_server_exceptions=False) as c:
        token = c.post("/api/v1/auth/login", json={"usuario": "recepcion", "clave": "Recepcion123*"}).json()["data"]["accessToken"]
        with patch(
            "app.repositories.cliente_repository.ClienteRepository.obtener_por_id",
            side_effect=RuntimeError("fallo inesperado"),
        ):
            r = c.get("/api/v1/clientes/CLI-0001", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 500
    cuerpo = r.json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["success"] is False
    assert cuerpo["errors"][0]["codigo"] == "ERR-500"


def test_body_invalido_responde_400_con_envelope(client):
    r = client.post("/api/v1/clientes", json={"tipoDocumento": "CC"})
    assert r.status_code == 400
    cuerpo = r.json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert all(e["codigo"] == "VAL-FORMATO" for e in cuerpo["errors"])
