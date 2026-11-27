"""Casos de prueba de HU-066 Registrar pago de cliente (Parcial 2, FUN-66)."""
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from app.domain.entities.factura import aplicar_pago
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


URL = "/api/v1/pagos/clientes"
CAMPOS_DATA = {"idPago", "idFactura", "valor", "saldoPendiente", "estadoFactura", "metodo", "referenciaComprobante"}
MSG_INVALIDOS = "No fue posible completar «Registrar pago de cliente»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar pago de cliente»: la operación viola una regla de negocio."
MSG_NO_EXISTE = "No fue posible completar «Registrar pago de cliente»: no existe el recurso indicado."
# Ejemplo del contrato: 141.312,50 que salda la factura. FAC-0001 vale 148.750, así que antes se abonan 7.437,50.
BODY = {
    "idFactura": "FAC-0001",
    "valor": 141312.5,
    "fechaPago": "2026-10-14",
    "metodo": "transferencia",
    "referenciaComprobante": "TRX-445566",
}
ABONO = {**BODY, "valor": 7437.5, "metodo": "efectivo", "referenciaComprobante": "REC-0001"}


def _estado_factura(client, id_factura="FAC-0001"):
    return client.get(f"/api/v1/facturas/{id_factura}").json()["data"]


def _anular(id_factura="FAC-0001"):
    from app.core.database import SessionLocal
    from app.domain.models.factura import FacturaModel

    with SessionLocal() as db:
        db.query(FacturaModel).filter_by(id_factura=id_factura).one().estado = "anulada"
        db.commit()


@pytest.fixture
def facturada(client):
    """FAC-0001 emitida de OS-0001 por 148.750 (80.000 mano de obra + 45.000 repuestos + IVA 19%)."""
    tec = _preparar_orden(client)
    _consumir(client, tec, _actividad(client, tec), 1)
    r = client.post(f"{ORDEN}/cerrar", json={"confirmarCierre": True, "notificarCliente": False})
    assert r.json()["data"]["idFactura"] == "FAC-0001"
    return client


@pytest.fixture
def abonada(facturada):
    """FAC-0001 pagada_parcial con saldo 141.312,50 (PAG-0001 por 7.437,50)."""
    assert facturada.post(URL, json=ABONO).status_code == 201
    return facturada


def test_caso1_pago_exitoso(abonada):
    r = abonada.post(URL, json=BODY)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Pago de cliente registrado correctamente"
    assert cuerpo["data"] == {
        "idPago": "PAG-0002",
        "idFactura": "FAC-0001",
        "valor": 141312.5,
        "saldoPendiente": 0.0,
        "estadoFactura": "pagada",
        "metodo": "transferencia",
        "referenciaComprobante": "TRX-445566",
    }


def test_caso2_contrato_json(abonada):
    cuerpo = abonada.post(URL, json=BODY).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    assert set(cuerpo["data"]) == CAMPOS_DATA
    assert isinstance(cuerpo["data"]["valor"], float) and isinstance(cuerpo["data"]["saldoPendiente"], float)


def test_caso3_valor_supera_saldo_rn11(facturada):
    r = facturada.post(URL, json={**BODY, "valor": 148750.01})
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "RN-11", "detalle": "Valor supera saldo pendiente RN-11"}]
    assert _estado_factura(facturada)["saldoPendiente"] == 148750.0  # no se tocó el saldo


def test_caso3_factura_pagada_no_admite_mas_pagos(abonada):
    abonada.post(URL, json=BODY)
    r = abonada.post(URL, json={**BODY, "valor": 1})
    assert r.status_code == 409
    assert r.json()["errors"][0]["codigo"] == "RN-11"


def test_caso4_factura_anulada(facturada):
    _anular()
    r = facturada.post(URL, json=BODY)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "VAL-NEGOCIO", "detalle": "Factura anulada"}]


def test_caso5_fallo_de_base_de_datos(abonada):
    with patch(
        "app.repositories.pago_cliente_repository.PagoClienteRepository.registrar",
        side_effect=OperationalError("INSERT", {}, Exception("BD caída")),
    ):
        r = abonada.post(URL, json=BODY)
    assert r.status_code == 503
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No fue posible completar la operación por indisponibilidad de la base de datos."
    assert cuerpo["errors"] == [{"campo": "persistencia", "codigo": "DB-DOWN", "detalle": "Base de datos no disponible"}]


def test_pago_parcial_deja_pagada_parcial(facturada):
    r = facturada.post(URL, json=ABONO)
    assert r.status_code == 201
    data = r.json()["data"]
    assert (data["idPago"], data["saldoPendiente"], data["estadoFactura"]) == ("PAG-0001", 141312.5, "pagada_parcial")
    factura = _estado_factura(facturada)  # HU-062 refleja el nuevo saldo y estado
    assert (factura["saldoPendiente"], factura["estado"]) == (141312.5, "pagada_parcial")


def test_pago_total_en_un_solo_pago(facturada):
    r = facturada.post(URL, json={**BODY, "valor": 148750.0})
    assert r.json()["data"]["estadoFactura"] == "pagada"
    assert _estado_factura(facturada)["estado"] == "pagada"


def test_el_pago_queda_persistido(abonada):
    from app.core.database import SessionLocal
    from app.domain.models.pago_cliente import PagoClienteModel

    abonada.post(URL, json=BODY)
    with SessionLocal() as db:
        p = db.query(PagoClienteModel).filter_by(id_pago="PAG-0002").one()
        assert (p.id_factura, float(p.valor), p.fecha_pago.isoformat(), p.metodo, p.referencia_comprobante) == (
            "FAC-0001", 141312.5, "2026-10-14", "transferencia", "TRX-445566",
        )


@pytest.mark.parametrize("metodo", ["efectivo", "transferencia", "tarjeta", "otros"])
def test_metodos_permitidos(facturada, metodo):
    assert facturada.post(URL, json={**ABONO, "metodo": metodo}).status_code == 201


def test_factura_inexistente(facturada):
    r = facturada.post(URL, json={**BODY, "idFactura": "FAC-9999"})
    assert r.status_code == 404
    assert r.json()["message"] == MSG_NO_EXISTE
    assert r.json()["errors"] == [{"campo": "idFactura", "codigo": "NOT-FOUND", "detalle": "Factura inexistente"}]


@pytest.mark.parametrize(
    ("cambio", "campo"),
    [
        ({"idFactura": "FAC-1"}, "idFactura"),
        ({"valor": 0}, "valor"),
        ({"valor": -100}, "valor"),
        ({"valor": 100.123}, "valor"),
        ({"metodo": "cheque"}, "metodo"),
        ({"referenciaComprobante": "   "}, "referenciaComprobante"),
    ],
)
def test_formato_invalido(facturada, cambio, campo):
    r = facturada.post(URL, json={**BODY, **cambio})
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_INVALIDOS
    assert (cuerpo["errors"][0]["campo"], cuerpo["errors"][0]["codigo"]) == (campo, "VAL-FORMATO")


@pytest.mark.parametrize(
    "body",
    [
        {k: v for k, v in BODY.items() if k != "referenciaComprobante"},
        {k: v for k, v in BODY.items() if k != "valor"},
        {**BODY, "fechaPago": "14/10/2026"},
        {**BODY, "valor": "mil"},
        {**BODY, "referenciaComprobante": "X" * 41},
        {**BODY, "idCliente": "CLI-0001"},
    ],
)
def test_campos_obligatorios_tipos_y_extras(facturada, body):
    r = facturada.post(URL, json=body)
    assert r.status_code == 400
    assert r.json()["errors"][0]["codigo"] == "VAL-FORMATO"


def test_administrador_puede_registrar(facturada, client_sin_token):
    r = client_sin_token.post(URL, json=ABONO, headers=_auth(client_sin_token, "admin", "Admin123*"))
    assert r.status_code == 201


@pytest.mark.parametrize(("usuario", "clave"), [("tecnico", "Tecnico123*"), ("inventario", "Inventario123*")])
def test_roles_no_autorizados(facturada, client_sin_token, usuario, clave):
    r = client_sin_token.post(URL, json=ABONO, headers=_auth(client_sin_token, usuario, clave))
    assert r.status_code == 403
    assert r.json()["errors"][0]["codigo"] == "AUTH-403"


def test_requiere_token(client_sin_token):
    r = client_sin_token.post(URL, json=BODY)
    assert r.status_code == 401
    assert r.json()["message"] == "No autorizado."
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"


# Pruebas unitarias de Domain: RN-11.
@pytest.mark.parametrize(
    ("saldo", "valor", "esperado"),
    [
        ("148750.00", "148750.00", (Decimal("0.00"), "pagada")),
        ("148750.00", "7437.50", (Decimal("141312.50"), "pagada_parcial")),
        ("0.03", "0.01", (Decimal("0.02"), "pagada_parcial")),
    ],
)
def test_unitaria_aplicar_pago_rn11(saldo, valor, esperado):
    assert aplicar_pago(Decimal(saldo), Decimal(valor)) == esperado
