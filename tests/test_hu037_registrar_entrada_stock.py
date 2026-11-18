"""Casos de prueba de HU-037 Registrar entrada de stock (Parcial #2, FUN-37)."""
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from tests.conftest import CAMPOS_ENVELOPE, iniciar_sesion

URL = "/api/v1/inventario/entradas"
REPUESTO = {
    "referencia": "PAS-FZ150",
    "nombre": "Pastillas freno delantero FZ 150",
    "idCategoria": "CAT-FRE",
    "costo": 28000.0,
    "precio": 45000.0,
    "stockMinimo": 2,
}
ENTRADA = {"referencia": "PAS-FZ150", "cantidad": 10, "idRecepcion": None, "ubicacion": "EST-A-03", "motivo": "ajuste_positivo"}
CAMPOS_DATA = {"idMovimiento", "tipo", "referencia", "cantidad", "stockResultante", "idRecepcion"}
MSG_INVALIDOS = "No fue posible completar «Registrar entrada de stock»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar entrada de stock»: la operación viola una regla de negocio."


@pytest.fixture
def inventario(client_sin_token):
    """El encargado de inventario registra las entradas; arranca con un repuesto en el catálogo."""
    client_sin_token.headers["Authorization"] = f"Bearer {iniciar_sesion(client_sin_token, 'inventario', 'Inventario123*')}"
    assert client_sin_token.post("/api/v1/repuestos", json=REPUESTO).status_code == 201
    return client_sin_token


def test_caso1_entrada_exitosa_acumula_stock(inventario):
    inventario.post(URL, json={**ENTRADA, "cantidad": 5})
    r = inventario.post(URL, json=ENTRADA)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Entrada de stock registrada correctamente"
    assert cuerpo["data"] == {
        "idMovimiento": "MOV-0002",
        "tipo": "ENTRADA",
        "referencia": "PAS-FZ150",
        "cantidad": 10,
        "stockResultante": 15,
        "idRecepcion": None,
    }


def test_caso2_contrato_json(inventario):
    cuerpo = inventario.post(URL, json=ENTRADA).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert set(cuerpo["data"]) == CAMPOS_DATA


def test_caso3_repuesto_inactivo(inventario):
    from app.core.database import SessionLocal
    from app.domain.models.repuesto import RepuestoModel

    with SessionLocal() as db:
        db.query(RepuestoModel).filter_by(referencia="PAS-FZ150").update({"estado": "inactivo"})
        db.commit()
    r = inventario.post(URL, json=ENTRADA)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "VAL-NEGOCIO", "detalle": "Repuesto inactivo"}]


@pytest.mark.parametrize("cantidad", [0, -3])
def test_caso4_cantidad_menor_o_igual_a_cero(inventario, cantidad):
    r = inventario.post(URL, json={**ENTRADA, "cantidad": cantidad})
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["errors"] == [{"campo": "cantidad", "codigo": "VAL-FORMATO", "detalle": "Cantidad <= 0"}]


def test_caso5_fallo_de_base_de_datos(inventario):
    with patch(
        "app.repositories.movimiento_inventario_repository.MovimientoInventarioRepository.registrar",
        side_effect=OperationalError("INSERT", {}, Exception("BD caída")),
    ):
        r = inventario.post(URL, json=ENTRADA)
    assert r.status_code == 503
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_cantidad_con_tres_decimales(inventario):
    r = inventario.post(URL, json={**ENTRADA, "cantidad": 2.125})
    assert r.status_code == 201
    assert r.json()["data"]["cantidad"] == 2.125
    assert r.json()["data"]["stockResultante"] == 2.125


def test_cantidad_con_mas_de_tres_decimales(inventario):
    r = inventario.post(URL, json={**ENTRADA, "cantidad": 1.0005})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "cantidad"


def test_motivo_no_valido(inventario):
    r = inventario.post(URL, json={**ENTRADA, "motivo": "regalo"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "motivo"


def test_referencia_inexistente(inventario):
    r = inventario.post(URL, json={**ENTRADA, "referencia": "NO-EXISTE"})
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "referencia"


def test_recepcion_no_disponible_en_esta_version(inventario):
    r = inventario.post(URL, json={**ENTRADA, "idRecepcion": "REC-0701"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "idRecepcion"


def test_referencia_sin_importar_mayusculas(inventario):
    r = inventario.post(URL, json={**ENTRADA, "referencia": "pas-fz150"})
    assert r.status_code == 201
    assert r.json()["data"]["referencia"] == "PAS-FZ150"


def test_movimiento_guarda_usuario_motivo_y_ubicacion(inventario):
    from app.core.database import SessionLocal
    from app.domain.models.movimiento_inventario import MovimientoInventarioModel

    inventario.post(URL, json=ENTRADA)
    with SessionLocal() as db:
        m = db.query(MovimientoInventarioModel).one()
    assert (m.tipo, m.usuario, m.motivo, m.ubicacion) == ("ENTRADA", "inventario", "ajuste_positivo", "EST-A-03")


def test_recepcion_no_puede_registrar_entradas(client):
    assert client.post(URL, json=ENTRADA).status_code == 403


def test_requiere_token(client_sin_token):
    assert client_sin_token.post(URL, json=ENTRADA).status_code == 401
