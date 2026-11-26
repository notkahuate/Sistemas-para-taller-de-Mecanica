"""Casos de prueba de HU-020 Cerrar y facturar orden de servicio (Parcial 2, FUN-20)."""
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

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
BODY = {"confirmarCierre": True, "notificarCliente": True}
CAMPOS_DATA = {"idOrden", "estado", "fechaCierre", "totales", "idFactura", "notificacionCliente"}
CAMPOS_TOTALES = {"manoObra", "repuestos", "subtotal", "impuestos", "descuentos", "total"}
MSG_INVALIDOS = "No fue posible completar «Cerrar y facturar orden de servicio»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Cerrar y facturar orden de servicio»: la operación viola una regla de negocio."
BASE = "/api/v1/ordenes-servicio/OS-0001"


def url(id_orden="OS-0001"):
    return f"/api/v1/ordenes-servicio/{id_orden}/cerrar"


def _auth(client, usuario, clave):
    return {"Authorization": f"Bearer {iniciar_sesion(client, usuario, clave)}"}


@pytest.fixture
def orden(client):
    """OS-0001 en_proceso con TEC-0001 (40.000/h) y 5 unidades de PAS-FZ150 (45.000) en stock.

    Devuelve los headers del técnico para completar el trabajo en cada prueba.
    """
    id_cliente = client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]
    id_moto = client.post("/api/v1/motocicletas", json={**MOTO, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    client.post(
        "/api/v1/ordenes-servicio",
        json={"idCliente": id_cliente, "idMotocicleta": id_moto, "motivoVisita": "Mantenimiento 5000 km", "fechaIngreso": "2026-11-20T08:30:00-05:00"},
    )
    client.post("/api/v1/tecnicos", json=TECNICO, headers=_auth(client, "admin", "Admin123*"))
    client.patch(f"{BASE}/tecnico", json={"idTecnico": "TEC-0001", "fechaAsignacion": "2026-11-20T09:00:00-05:00"})
    inventario = _auth(client, "inventario", "Inventario123*")
    client.post("/api/v1/repuestos", json=REPUESTO, headers=inventario)
    client.post(
        "/api/v1/inventario/entradas",
        json={"referencia": "PAS-FZ150", "cantidad": 5, "idRecepcion": None, "ubicacion": "EST-A-03", "motivo": "ajuste_positivo"},
        headers=inventario,
    )
    return _auth(client, "tecnico", "Tecnico123*")


def _diagnostico(client, tec):
    client.post(f"{BASE}/diagnosticos", json=DIAGNOSTICO, headers=tec)


def _actividad(client, tec, estado="completada", inicio="09:15", fin="11:15"):
    r = client.post(
        f"{BASE}/actividades",
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


@pytest.fixture
def lista(client, orden):
    """Orden lista para cerrar: diagnóstico, una actividad completada de 120 min y 1 pastilla consumida.

    Mano de obra 120/60 * 40.000 = 80.000; repuestos 1 * 45.000 = 45.000 (los valores del ejemplo del contrato).
    """
    _diagnostico(client, orden)
    id_actividad = _actividad(client, orden)
    client.post(
        f"{BASE}/repuestos-utilizados",
        json={"idActividad": id_actividad, "referencia": "PAS-FZ150", "cantidad": 1, "motivo": "consumo_orden"},
        headers=orden,
    )
    return client


def test_caso1_cierre_exitoso(lista):
    r = lista.post(url(), json=BODY)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Orden de servicio cerrada y factura generada correctamente"
    data = cuerpo["data"]
    assert data["fechaCierre"].endswith("-05:00")
    assert {k: v for k, v in data.items() if k != "fechaCierre"} == {
        "idOrden": "OS-0001",
        "estado": "finalizada",
        "totales": {
            "manoObra": 80000.0,
            "repuestos": 45000.0,
            "subtotal": 125000.0,
            "impuestos": 23750.0,
            "descuentos": 0.0,
            "total": 148750.0,
        },
        "idFactura": "FAC-0001",
        "notificacionCliente": "pendiente",
    }


def test_caso2_contrato_json(lista):
    cuerpo = lista.post(url(), json=BODY).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    assert set(cuerpo["data"]) == CAMPOS_DATA
    assert set(cuerpo["data"]["totales"]) == CAMPOS_TOTALES


def test_caso3_sin_diagnostico_rn05(client, orden):
    _actividad(client, orden)
    r = client.post(url(), json=BODY)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [
        {"campo": "request", "codigo": "RN-05", "detalle": "Sin diagnóstico o actividades incompletas RN-05"}
    ]


@pytest.mark.parametrize("con_actividad", [False, True])
def test_caso3_actividades_incompletas_rn05(client, orden, con_actividad):
    _diagnostico(client, orden)
    if con_actividad:
        _actividad(client, orden, estado="en_ejecucion")  # ninguna completada
    r = client.post(url(), json=BODY)
    assert r.status_code == 409
    assert r.json()["errors"][0]["codigo"] == "RN-05"


def test_caso4_orden_ya_finalizada_rn02(lista):
    lista.post(url(), json=BODY)
    r = lista.post(url(), json=BODY)
    assert r.status_code == 409
    assert r.json()["message"] == MSG_REGLA
    assert r.json()["errors"] == [{"campo": "request", "codigo": "RN-02", "detalle": "Orden ya finalizada RN-02"}]


def test_caso5_fallo_de_base_de_datos(lista):
    with patch(
        "app.repositories.orden_servicio_repository.OrdenServicioRepository.cerrar_y_facturar",
        side_effect=OperationalError("UPDATE", {}, Exception("BD caída")),
    ):
        r = lista.post(url(), json=BODY)
    assert r.status_code == 503
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"
    # la orden no quedó a medias
    assert lista.get(BASE).json()["data"]["estado"] == "en_proceso"


def test_la_orden_queda_finalizada_y_la_factura_emitida(lista):
    from app.core.database import SessionLocal
    from app.domain.models.factura import FacturaModel

    lista.post(url(), json=BODY)
    estado = lista.get(BASE).json()["data"]
    assert estado["estado"] == "finalizada"
    assert estado["fechaCierre"] is not None  # HU-018 ya muestra la fecha de cierre
    with SessionLocal() as db:
        f = db.query(FacturaModel).filter_by(id_factura="FAC-0001").one()
        assert (f.id_orden, f.id_cliente, f.estado) == ("OS-0001", "CLI-0001", "emitida")
        assert (float(f.base_iva), float(f.saldo_pendiente)) == (125000.0, 148750.0)


def test_suma_varias_actividades_y_repuestos(client, orden):
    _diagnostico(client, orden)
    a1 = _actividad(client, orden, inicio="08:00", fin="09:30")  # 90 min = 60.000
    _actividad(client, orden, estado="en_ejecucion", inicio="10:00", fin="10:45")  # 45 min = 30.000
    for cantidad in (2, 0.5):
        client.post(
            f"{BASE}/repuestos-utilizados",
            json={"idActividad": a1, "referencia": "PAS-FZ150", "cantidad": cantidad, "motivo": "consumo_orden"},
            headers=orden,
        )
    totales = client.post(url(), json=BODY).json()["data"]["totales"]
    assert totales == {
        "manoObra": 90000.0,
        "repuestos": 112500.0,  # 2,5 * 45.000
        "subtotal": 202500.0,
        "impuestos": 38475.0,
        "descuentos": 0.0,
        "total": 240975.0,
    }


def test_actividad_sin_tiempo_no_suma_mano_obra(client, orden):
    _diagnostico(client, orden)
    _actividad(client, orden, fin=None)
    totales = client.post(url(), json=BODY).json()["data"]["totales"]
    assert (totales["manoObra"], totales["total"]) == (0.0, 0.0)


def test_sin_notificacion_al_cliente(lista):
    r = lista.post(url(), json={**BODY, "notificarCliente": False})
    assert r.json()["data"]["notificacionCliente"] == "no_solicitada"


def test_cierre_no_confirmado(lista):
    r = lista.post(url(), json={**BODY, "confirmarCierre": False})
    assert r.status_code == 400
    assert r.json()["message"] == MSG_INVALIDOS
    assert r.json()["errors"][0]["campo"] == "confirmarCierre"


def test_orden_recibida_rn02(client):
    id_cliente = client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]
    id_moto = client.post("/api/v1/motocicletas", json={**MOTO, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    client.post(
        "/api/v1/ordenes-servicio",
        json={"idCliente": id_cliente, "idMotocicleta": id_moto, "motivoVisita": "Revisión", "fechaIngreso": "2026-11-20T08:30:00-05:00"},
    )
    r = client.post(url(), json=BODY)
    assert r.status_code == 409
    assert r.json()["errors"][0]["detalle"] == "Orden no está en_proceso RN-02"


def test_orden_inexistente_y_mal_formada(lista):
    assert lista.post(url("OS-9999"), json=BODY).status_code == 404
    r = lista.post(url("OS-1"), json=BODY)
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "idOrden"


def test_campos_obligatorios_y_tipos(lista):
    assert lista.post(url(), json={"confirmarCierre": True}).status_code == 400
    assert lista.post(url(), json={**BODY, "confirmarCierre": "true"}).status_code == 400
    assert lista.post(url(), json={**BODY, "descuento": 10}).status_code == 400


def test_administrador_puede_cerrar(lista, client_sin_token):
    r = client_sin_token.post(url(), json=BODY, headers=_auth(client_sin_token, "admin", "Admin123*"))
    assert r.status_code == 200


def test_tecnico_no_puede_cerrar(lista, client_sin_token):
    r = client_sin_token.post(url(), json=BODY, headers=_auth(client_sin_token, "tecnico", "Tecnico123*"))
    assert r.status_code == 403


def test_requiere_token(client_sin_token):
    r = client_sin_token.post(url(), json=BODY)
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"
