"""Casos de prueba de HU-061 Generar factura de servicio (Parcial 2, FUN-61)."""
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from app.domain.entities.factura import calcular_totales
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
URL = "/api/v1/facturas"
ORDEN = "/api/v1/ordenes-servicio/OS-0001"
BODY = {"idOrden": "OS-0001", "correoEnvio": "carlos.perez@email.com"}
CAMPOS_DATA = {
    "idFactura", "idOrden", "idCliente", "manoObra", "repuestos", "subtotal", "descuentos",
    "baseIva", "impuestos", "total", "saldoPendiente", "estado", "fechaEmision",
}
MSG_INVALIDOS = "No fue posible completar «Generar factura de servicio»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Generar factura de servicio»: la operación viola una regla de negocio."


def _auth(client, usuario, clave):
    return {"Authorization": f"Bearer {iniciar_sesion(client, usuario, clave)}"}


@pytest.fixture
def en_proceso(client):
    """OS-0001 en_proceso con diagnóstico, una actividad completada de 120 min (TEC-0001 a 40.000/h = 80.000)
    y 1 pastilla consumida (45.000): los valores del ejemplo del contrato."""
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
    r = client.post(
        f"{ORDEN}/actividades",
        json={"nombre": "Cambio de pastillas y aceite", "estado": "completada", "horaInicio": "2026-11-20T09:15:00-05:00"},
        headers=tec,
    )
    id_actividad = r.json()["data"]["idActividad"]
    client.patch(
        f"/api/v1/actividades/{id_actividad}/mano-obra",
        json={"horaInicio": "2026-11-20T09:15:00-05:00", "horaFin": "2026-11-20T11:15:00-05:00"},
        headers=tec,
    )
    client.post(
        f"{ORDEN}/repuestos-utilizados",
        json={"idActividad": id_actividad, "referencia": "PAS-FZ150", "cantidad": 1, "motivo": "consumo_orden"},
        headers=tec,
    )
    return client


@pytest.fixture
def con_factura(en_proceso):
    """OS-0001 cerrada con HU-020, que ya generó FAC-0001 emitida."""
    r = en_proceso.post(f"{ORDEN}/cerrar", json={"confirmarCierre": True, "notificarCliente": False})
    assert r.json()["data"]["idFactura"] == "FAC-0001"
    return en_proceso


@pytest.fixture
def lista(con_factura):
    """OS-0001 finalizada sin factura vigente: FAC-0001 quedó anulada (lo que hará HU-063)."""
    from app.core.database import SessionLocal
    from app.domain.models.factura import FacturaModel

    with SessionLocal() as db:
        db.query(FacturaModel).filter_by(id_factura="FAC-0001").one().estado = "anulada"
        db.commit()
    return con_factura


def test_caso1_generacion_exitosa(lista):
    r = lista.post(URL, json=BODY)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Factura de servicio generada correctamente"
    data = cuerpo["data"]
    assert data["fechaEmision"].endswith("-05:00")
    assert {k: v for k, v in data.items() if k != "fechaEmision"} == {
        "idFactura": "FAC-0002",
        "idOrden": "OS-0001",
        "idCliente": "CLI-0001",
        "manoObra": 80000.0,
        "repuestos": 45000.0,
        "subtotal": 125000.0,
        "descuentos": 0.0,
        "baseIva": 125000.0,
        "impuestos": 23750.0,
        "total": 148750.0,
        "saldoPendiente": 148750.0,
        "estado": "emitida",
    }


def test_caso2_contrato_json(lista):
    cuerpo = lista.post(URL, json=BODY).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    assert set(cuerpo["data"]) == CAMPOS_DATA
    for campo in CAMPOS_DATA - {"idFactura", "idOrden", "idCliente", "estado", "fechaEmision"}:
        assert isinstance(cuerpo["data"][campo], float)


def test_caso3_orden_no_finalizada_rn05(en_proceso):
    r = en_proceso.post(URL, json=BODY)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "RN-05", "detalle": "Orden no finalizada RN-05"}]


def test_caso4_orden_ya_tiene_factura_emitida(con_factura):
    r = con_factura.post(URL, json=BODY)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [
        {"campo": "request", "codigo": "VAL-NEGOCIO", "detalle": "La orden ya tiene factura emitida"}
    ]


def test_caso4_no_se_duplica_al_generar_dos_veces(lista):
    assert lista.post(URL, json=BODY).status_code == 201
    r = lista.post(URL, json=BODY)
    assert r.status_code == 409
    assert r.json()["errors"][0]["codigo"] == "VAL-NEGOCIO"


def test_caso5_fallo_de_base_de_datos(lista):
    with patch(
        "app.repositories.factura_repository.FacturaRepository.crear",
        side_effect=OperationalError("INSERT", {}, Exception("BD caída")),
    ):
        r = lista.post(URL, json=BODY)
    assert r.status_code == 503
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No fue posible completar la operación por indisponibilidad de la base de datos."
    assert cuerpo["errors"] == [{"campo": "persistencia", "codigo": "DB-DOWN", "detalle": "Base de datos no disponible"}]


def test_la_factura_queda_persistida_emitida(lista):
    from app.core.database import SessionLocal
    from app.domain.models.factura import FacturaModel

    lista.post(URL, json=BODY)
    with SessionLocal() as db:
        f = db.query(FacturaModel).filter_by(id_factura="FAC-0002").one()
        assert (f.id_orden, f.id_cliente, f.estado) == ("OS-0001", "CLI-0001", "emitida")
        assert float(f.saldo_pendiente) == float(f.total) == 148750.0  # RN-11


def test_orden_inexistente(lista):
    r = lista.post(URL, json={**BODY, "idOrden": "OS-9999"})
    assert r.status_code == 404
    assert r.json()["errors"][0]["codigo"] == "NOT-FOUND"


@pytest.mark.parametrize(
    ("cambio", "campo"),
    [({"idOrden": "OS-1"}, "idOrden"), ({"correoEnvio": "carlos.perez"}, "correoEnvio")],
)
def test_formato_invalido(lista, cambio, campo):
    r = lista.post(URL, json={**BODY, **cambio})
    assert r.status_code == 400
    assert r.json()["message"] == MSG_INVALIDOS
    assert r.json()["errors"] == [{"campo": campo, "codigo": "VAL-FORMATO", "detalle": r.json()["errors"][0]["detalle"]}]


@pytest.mark.parametrize(
    "body",
    [
        {"idOrden": "OS-0001"},
        {"correoEnvio": "carlos.perez@email.com"},
        {**BODY, "idOrden": 1},
        {**BODY, "descuentos": 1000},
    ],
)
def test_campos_obligatorios_tipos_y_extras(lista, body):
    r = lista.post(URL, json=body)
    assert r.status_code == 400
    assert r.json()["errors"][0]["codigo"] == "VAL-FORMATO"


def test_administrador_puede_generar(lista, client_sin_token):
    r = client_sin_token.post(URL, json=BODY, headers=_auth(client_sin_token, "admin", "Admin123*"))
    assert r.status_code == 201


@pytest.mark.parametrize(("usuario", "clave"), [("tecnico", "Tecnico123*"), ("inventario", "Inventario123*")])
def test_roles_no_autorizados(lista, client_sin_token, usuario, clave):
    r = client_sin_token.post(URL, json=BODY, headers=_auth(client_sin_token, usuario, clave))
    assert r.status_code == 403
    assert r.json()["errors"][0]["codigo"] == "AUTH-403"


def test_requiere_token(client_sin_token):
    r = client_sin_token.post(URL, json=BODY)
    assert r.status_code == 401
    assert r.json()["message"] == "No autorizado."
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"


# Pruebas unitarias de Domain: RN-05 (mano de obra + repuestos - descuentos + IVA 19%) y redondeo a 2 decimales.
def test_unitaria_calculo_del_ejemplo_del_contrato():
    t = calcular_totales(Decimal("80000"), Decimal("45000"))
    assert (t["subtotal"], t["base_iva"], t["impuestos"], t["total"]) == (
        Decimal("125000.00"), Decimal("125000.00"), Decimal("23750.00"), Decimal("148750.00"),
    )


def test_unitaria_descuentos_y_redondeo():
    t = calcular_totales(Decimal("33333.335"), Decimal("0.01"), Decimal("1000"))
    assert t["mano_obra"] == Decimal("33333.34")
    assert t["base_iva"] == Decimal("32333.35")
    assert t["impuestos"] == Decimal("6143.34")  # 32333.35 * 0.19 = 6143.3365
    assert t["total"] == Decimal("38476.69")
