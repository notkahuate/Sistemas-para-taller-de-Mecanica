"""Casos de prueba de HU-062 Consultar factura (Parcial 2, FUN-62)."""
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from app.domain.entities.factura import ID_FACTURA_RE
from tests.conftest import CAMPOS_ENVELOPE, iniciar_sesion

CLIENTE = {
    "tipoDocumento": "CC",
    "numeroDocumento": "1098765432",
    "nombreCompleto": "Carlos Andrés Pérez Gómez",
    "telefono": "3001234567",
    "correo": "carlos.perez@email.com",
    "direccion": "Calle 45 # 12-30, Bucaramanga",
}
MOTO = {"placa": "ABC12D", "vin": None, "marca": "Yamaha", "linea": "FZ 2.0", "anio": 2023, "cilindraje": 150, "color": "Azul"}
TECNICO = {
    "tipoDocumento": "CC",
    "numeroDocumento": "109111222",
    "nombreCompleto": "Luis Martínez",
    "telefono": "3002223344",
    "correo": "luis.martinez@motoservice.com",
    "cargo": "Técnico de frenos",
    "fechaIngreso": "2026-02-01",
    "tarifaHoraria": 40000.0,
}
REPUESTO = {
    "referencia": "PAS-FZ150",
    "nombre": "Pastillas freno delantero FZ 150",
    "descripcion": "Juego original",
    "idCategoria": "CAT-FRE",
    "idProveedor": "PRV-08",
    "costo": 28000.0,
    "precio": 45000.0,
    "stockMinimo": 2,
}
DIAGNOSTICO = {
    "hallazgos": "Pastillas de freno delantero al 20% de vida útil. Aceite oscuro a 5200 km.",
    "pruebas": "Prueba de frenado a 40 km/h; inspección visual de motor.",
    "diagnostico": "Desgaste de pastillas delanteras y aceite vencido por kilometraje.",
    "recomendaciones": "Cambio de pastillas y aceite 10W40.",
}
ORDEN = "/api/v1/ordenes-servicio/OS-0001"
CAMPOS_DATA = {"idFactura", "idOrden", "idCliente", "estado", "total", "saldoPendiente", "pagos", "detalle"}
MSG_INVALIDOS = "No fue posible completar «Consultar factura»: los datos enviados no son válidos."
MSG_NO_EXISTE = "No fue posible completar «Consultar factura»: no existe el recurso indicado."


def url(id_factura="FAC-0001"):
    return f"/api/v1/facturas/{id_factura}"


def _auth(client, usuario, clave):
    return {"Authorization": f"Bearer {iniciar_sesion(client, usuario, clave)}"}


def _preparar_orden(client):
    """OS-0001 en_proceso con TEC-0001 (40.000/h), diagnóstico y 5 pastillas PAS-FZ150 (45.000) en stock."""
    id_cliente = client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]
    id_moto = client.post("/api/v1/motocicletas", json={**MOTO, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    client.post(
        "/api/v1/ordenes-servicio",
        json={"idCliente": id_cliente, "idMotocicleta": id_moto, "motivoVisita": "Mantenimiento 5000 km", "fechaIngreso": "2026-11-20T08:30:00-05:00"},
    )
    client.post("/api/v1/tecnicos", json=TECNICO, headers=_auth(client, "admin", "Admin123*"))
    client.patch(f"{ORDEN}/tecnico", json={"idTecnico": "TEC-0001", "fechaAsignacion": "2026-11-20T09:00:00-05:00"})
    inventario = _auth(client, "inventario", "Inventario123*")
    client.post("/api/v1/repuestos", json=REPUESTO, headers=inventario)
    client.post(
        "/api/v1/inventario/entradas",
        json={"referencia": "PAS-FZ150", "cantidad": 5, "idRecepcion": None, "ubicacion": "EST-A-03", "motivo": "ajuste_positivo"},
        headers=inventario,
    )
    tec = _auth(client, "tecnico", "Tecnico123*")
    client.post(f"{ORDEN}/diagnosticos", json=DIAGNOSTICO, headers=tec)
    return tec


def _actividad(client, tec, inicio="09:15", fin="11:15", estado="completada"):
    r = client.post(
        f"{ORDEN}/actividades",
        json={"nombre": "Cambio de pastillas y aceite", "estado": estado, "horaInicio": f"2026-11-20T{inicio}:00-05:00"},
        headers=tec,
    )
    id_actividad = r.json()["data"]["idActividad"]
    if fin:
        client.patch(
            f"/api/v1/actividades/{id_actividad}/mano-obra",
            json={"horaInicio": f"2026-11-20T{inicio}:00-05:00", "horaFin": f"2026-11-20T{fin}:00-05:00"},
            headers=tec,
        )
    return id_actividad


def _consumir(client, tec, id_actividad, cantidad):
    client.post(
        f"{ORDEN}/repuestos-utilizados",
        json={"idActividad": id_actividad, "referencia": "PAS-FZ150", "cantidad": cantidad, "motivo": "consumo_orden"},
        headers=tec,
    )


def _cerrar(client):
    r = client.post(f"{ORDEN}/cerrar", json={"confirmarCierre": True, "notificarCliente": False})
    return r.json()["data"]["idFactura"]


@pytest.fixture
def facturada(client):
    """FAC-0001 de OS-0001: una actividad de 120 min (80.000) y 1 pastilla (45.000), total 148.750 (HU-020/HU-061)."""
    tec = _preparar_orden(client)
    _consumir(client, tec, _actividad(client, tec), 1)
    assert _cerrar(client) == "FAC-0001"
    return client


def test_caso1_consulta_exitosa(facturada):
    r = facturada.get(url())
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Consulta de factura exitosa"
    assert cuerpo["data"] == {
        "idFactura": "FAC-0001",
        "idOrden": "OS-0001",
        "idCliente": "CLI-0001",
        "estado": "emitida",
        "total": 148750.0,
        "saldoPendiente": 148750.0,
        "pagos": [],
        "detalle": {
            "manoObra": [{"idActividad": "ACT-0001", "minutos": 120, "valor": 80000.0}],
            "repuestos": [{"referencia": "PAS-FZ150", "cantidad": 1, "precio": 45000.0}],
        },
    }


def test_caso2_contrato_json(facturada):
    cuerpo = facturada.get(url()).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    data = cuerpo["data"]
    assert set(data) == CAMPOS_DATA
    assert set(data["detalle"]) == {"manoObra", "repuestos"}
    assert set(data["detalle"]["manoObra"][0]) == {"idActividad", "minutos", "valor"}
    assert set(data["detalle"]["repuestos"][0]) == {"referencia", "cantidad", "precio"}
    assert isinstance(data["total"], float) and isinstance(data["saldoPendiente"], float)
    assert isinstance(data["pagos"], list)


def test_caso3_factura_inexistente(facturada):
    r = facturada.get(url("FAC-9999"))
    assert r.status_code == 404
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_NO_EXISTE
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "idFactura", "codigo": "NOT-FOUND", "detalle": "Factura inexistente"}]


@pytest.mark.parametrize("id_factura", ["FAC-1", "FAC-00001", "fac-0001", "OS-0001", "FAC-ABCD"])
def test_caso4_id_factura_mal_formado(facturada, id_factura):
    r = facturada.get(url(id_factura))
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "VAL-FORMATO", "detalle": "IdFactura mal formado FAC-NNNN"}]


def test_caso5_fallo_de_base_de_datos(facturada):
    with patch(
        "app.repositories.factura_repository.FacturaRepository.obtener_por_id",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = facturada.get(url())
    assert r.status_code == 503
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No fue posible completar la operación por indisponibilidad de la base de datos."
    assert cuerpo["errors"] == [{"campo": "persistencia", "codigo": "DB-DOWN", "detalle": "Base de datos no disponible"}]


def test_detalle_con_varias_actividades_y_repuestos(client):
    """RN-05: el detalle muestra solo lo ejecutado; la actividad sin tiempo registrado no se cobra."""
    tec = _preparar_orden(client)
    a1 = _actividad(client, tec, inicio="08:00", fin="09:30")  # 90 min = 60.000
    _actividad(client, tec, inicio="09:40", fin=None, estado="en_ejecucion")  # sin tiempo: no se cobra
    _actividad(client, tec, inicio="10:00", fin="10:45")  # 45 min = 30.000
    _consumir(client, tec, a1, 2)
    _consumir(client, tec, a1, 0.5)
    _cerrar(client)
    data = client.get(url()).json()["data"]
    assert data["detalle"] == {
        "manoObra": [
            {"idActividad": "ACT-0001", "minutos": 90, "valor": 60000.0},
            {"idActividad": "ACT-0003", "minutos": 45, "valor": 30000.0},
        ],
        "repuestos": [
            {"referencia": "PAS-FZ150", "cantidad": 2, "precio": 45000.0},
            {"referencia": "PAS-FZ150", "cantidad": 0.5, "precio": 45000.0},
        ],
    }
    # el detalle cuadra con los totales de la factura
    mano_obra = sum(m["valor"] for m in data["detalle"]["manoObra"])
    repuestos = sum(r["cantidad"] * r["precio"] for r in data["detalle"]["repuestos"])
    assert round((mano_obra + repuestos) * 1.19, 2) == data["total"] == 240975.0


def test_factura_anulada_se_puede_consultar(facturada):
    from app.core.database import SessionLocal
    from app.domain.models.factura import FacturaModel

    with SessionLocal() as db:
        db.query(FacturaModel).filter_by(id_factura="FAC-0001").one().estado = "anulada"
        db.commit()
    r = facturada.get(url())
    assert r.status_code == 200
    assert r.json()["data"]["estado"] == "anulada"


def test_consulta_factura_generada_con_hu061(facturada):
    from app.core.database import SessionLocal
    from app.domain.models.factura import FacturaModel

    with SessionLocal() as db:
        db.query(FacturaModel).filter_by(id_factura="FAC-0001").one().estado = "anulada"
        db.commit()
    facturada.post("/api/v1/facturas", json={"idOrden": "OS-0001", "correoEnvio": "carlos.perez@email.com"})
    data = facturada.get(url("FAC-0002")).json()["data"]
    assert (data["idFactura"], data["estado"], data["total"]) == ("FAC-0002", "emitida", 148750.0)


def test_administrador_puede_consultar(facturada, client_sin_token):
    r = client_sin_token.get(url(), headers=_auth(client_sin_token, "admin", "Admin123*"))
    assert r.status_code == 200


@pytest.mark.parametrize(("usuario", "clave"), [("tecnico", "Tecnico123*"), ("inventario", "Inventario123*")])
def test_roles_no_autorizados(facturada, client_sin_token, usuario, clave):
    r = client_sin_token.get(url(), headers=_auth(client_sin_token, usuario, clave))
    assert r.status_code == 403
    assert r.json()["errors"][0]["codigo"] == "AUTH-403"


def test_requiere_token(client_sin_token):
    r = client_sin_token.get(url())
    assert r.status_code == 401
    assert r.json()["message"] == "No autorizado."
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"


# Prueba unitaria de Domain: formato FAC-NNNN del idFactura.
@pytest.mark.parametrize(("valor", "valido"), [("FAC-0001", True), ("FAC-3310", True), ("FAC-1", False), ("FAC-0001 ", False)])
def test_unitaria_formato_id_factura(valor, valido):
    assert bool(ID_FACTURA_RE.match(valor)) is valido
