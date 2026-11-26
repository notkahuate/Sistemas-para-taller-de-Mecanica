"""Casos de prueba de HU-027 Registrar repuestos utilizados (Parcial 2, FUN-27)."""
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
ACTIVIDAD = {"nombre": "Cambio de pastillas de freno delanteras", "estado": "en_ejecucion", "horaInicio": "2026-11-20T09:15:00-05:00"}
BODY = {"idActividad": "ACT-0001", "referencia": "PAS-FZ150", "cantidad": 1, "motivo": "consumo_orden"}
CAMPOS_DATA = {"idConsumo", "idOrden", "idActividad", "referencia", "cantidad", "stockResultante", "precioUnitario", "idMovimiento"}
MSG_INVALIDOS = "No fue posible completar «Registrar repuestos utilizados»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar repuestos utilizados»: la operación viola una regla de negocio."


def url(id_orden="OS-0001"):
    return f"/api/v1/ordenes-servicio/{id_orden}/repuestos-utilizados"


def _auth(client, usuario, clave):
    return {"Authorization": f"Bearer {iniciar_sesion(client, usuario, clave)}"}


def _orden(client, motivo="Ruido en frenos"):
    id_cliente = client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]
    id_moto = client.post("/api/v1/motocicletas", json={**MOTO, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    client.post(
        "/api/v1/ordenes-servicio",
        json={"idCliente": id_cliente, "idMotocicleta": id_moto, "motivoVisita": motivo, "fechaIngreso": "2026-11-20T08:30:00-05:00"},
    )


@pytest.fixture
def tecnico(client):
    """OS-0001 en_proceso con TEC-0001 (HU-017), actividad ACT-0001 (HU-026) y 5 unidades de PAS-FZ150 en stock (HU-031/HU-037)."""
    _orden(client)
    admin = _auth(client, "admin", "Admin123*")
    client.post("/api/v1/tecnicos", json=TECNICO, headers=admin)
    client.patch("/api/v1/ordenes-servicio/OS-0001/tecnico", json={"idTecnico": "TEC-0001", "fechaAsignacion": "2026-11-20T09:00:00-05:00"})
    tec = _auth(client, "tecnico", "Tecnico123*")
    client.post("/api/v1/ordenes-servicio/OS-0001/actividades", json=ACTIVIDAD, headers=tec)
    inventario = _auth(client, "inventario", "Inventario123*")
    client.post("/api/v1/repuestos", json=REPUESTO, headers=inventario)
    client.post(
        "/api/v1/inventario/entradas",
        json={"referencia": "PAS-FZ150", "cantidad": 5, "idRecepcion": None, "ubicacion": "EST-A-03", "motivo": "ajuste_positivo"},
        headers=inventario,
    )
    return tec


def _actualizar(modelo_ruta, filtro, cambios):
    from app.core.database import SessionLocal

    modulo, clase = modelo_ruta
    modelo = getattr(__import__(modulo, fromlist=[clase]), clase)
    with SessionLocal() as db:
        db.query(modelo).filter_by(**filtro).update(cambios)
        db.commit()


ORDEN = ("app.domain.models.orden_servicio", "OrdenServicioModel")
REPUESTO_M = ("app.domain.models.repuesto", "RepuestoModel")


def test_caso1_registro_exitoso(client, tecnico):
    r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Repuestos utilizados registrados correctamente"
    assert cuerpo["data"] == {
        "idConsumo": "CON-0001",
        "idOrden": "OS-0001",
        "idActividad": "ACT-0001",
        "referencia": "PAS-FZ150",
        "cantidad": 1,
        "stockResultante": 4,
        "precioUnitario": 45000.0,
        "idMovimiento": "MOV-0002",
    }


def test_caso2_contrato_json(client, tecnico):
    cuerpo = client.post(url(), json=BODY, headers=tecnico).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    assert set(cuerpo["data"]) == CAMPOS_DATA


def test_caso3_stock_insuficiente_rn03(client, tecnico):
    r = client.post(url(), json={**BODY, "cantidad": 6}, headers=tecnico)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [
        {"campo": "cantidad", "codigo": "RN-03", "detalle": "Stock insuficiente RN-03: disponible 5, solicitado 6"}
    ]


def test_caso4_orden_finalizada_rn02(client, tecnico):
    _actualizar(ORDEN, {"id_orden": "OS-0001"}, {"estado": "finalizada"})
    r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 409
    assert r.json()["message"] == MSG_REGLA
    assert r.json()["errors"] == [{"campo": "request", "codigo": "RN-02", "detalle": "Orden finalizada RN-02"}]


def test_caso5_fallo_de_base_de_datos(client, tecnico):
    with patch(
        "app.repositories.consumo_repuesto_repository.ConsumoRepuestoRepository.registrar",
        side_effect=OperationalError("INSERT", {}, Exception("BD caída")),
    ):
        r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 503
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_descuenta_stock_y_crea_movimiento_de_salida(client, tecnico):
    from app.core.database import SessionLocal
    from app.domain.models.movimiento_inventario import MovimientoInventarioModel

    client.post(url(), json={**BODY, "cantidad": 2}, headers=tecnico)
    r = client.post(url(), json={**BODY, "cantidad": 3}, headers=tecnico)
    assert r.json()["data"]["stockResultante"] == 0
    with SessionLocal() as db:
        salida = db.query(MovimientoInventarioModel).filter_by(id_movimiento="MOV-0003").one()
        assert (salida.tipo, salida.motivo, salida.usuario) == ("SALIDA", "consumo_orden", "tecnico")
    # ya no queda stock: RN-03
    assert client.post(url(), json=BODY, headers=tecnico).json()["errors"][0]["codigo"] == "RN-03"


def test_stock_insuficiente_no_deja_movimiento(client, tecnico):
    from app.core.database import SessionLocal
    from app.domain.models.movimiento_inventario import MovimientoInventarioModel

    client.post(url(), json={**BODY, "cantidad": 99}, headers=tecnico)
    with SessionLocal() as db:
        assert db.query(MovimientoInventarioModel).count() == 1  # solo la entrada inicial


def test_cantidad_con_decimales(client, tecnico):
    r = client.post(url(), json={**BODY, "cantidad": 0.5}, headers=tecnico)
    assert r.status_code == 201
    assert (r.json()["data"]["cantidad"], r.json()["data"]["stockResultante"]) == (0.5, 4.5)


def test_orden_recibida_sin_actividades_responde_404(client):
    """Una orden recibida aún no tiene actividades (HU-026 las exige en_proceso): la actividad no existe."""
    _orden(client)
    r = client.post(url(), json=BODY, headers=_auth(client, "admin", "Admin123*"))
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "idActividad"


def test_orden_recibida_rn02(client, tecnico):
    _actualizar(ORDEN, {"id_orden": "OS-0001"}, {"estado": "recibida"})
    r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 409
    assert r.json()["errors"][0]["detalle"] == "Orden no está en_proceso RN-02"


def test_repuesto_inactivo(client, tecnico):
    _actualizar(REPUESTO_M, {"referencia": "PAS-FZ150"}, {"estado": "inactivo"})
    r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 409
    assert r.json()["errors"][0]["detalle"] == "Repuesto inactivo"


@pytest.mark.parametrize(
    "ruta, cambios, campo",
    [
        ("OS-0009", {}, "idOrden"),
        ("OS-0001", {"idActividad": "ACT-0099"}, "idActividad"),
        ("OS-0001", {"referencia": "NOEXISTE-1"}, "referencia"),
    ],
)
def test_no_encontrados(client, tecnico, ruta, cambios, campo):
    r = client.post(url(ruta), json={**BODY, **cambios}, headers=tecnico)
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == campo


@pytest.mark.parametrize(
    "ruta, cambios, campo",
    [
        ("OS-1", {}, "idOrden"),
        ("OS-0001", {"idActividad": "4410"}, "idActividad"),
        ("OS-0001", {"cantidad": 0}, "cantidad"),
        ("OS-0001", {"cantidad": -1}, "cantidad"),
        ("OS-0001", {"cantidad": 1.0005}, "cantidad"),
        ("OS-0001", {"motivo": "ajuste_negativo"}, "motivo"),
    ],
)
def test_formatos_invalidos(client, tecnico, ruta, cambios, campo):
    r = client.post(url(ruta), json={**BODY, **cambios}, headers=tecnico)
    assert r.status_code == 400
    assert r.json()["message"] == MSG_INVALIDOS
    assert r.json()["errors"][0]["campo"] == campo


def test_consulta_de_orden_cuenta_repuestos_consumidos(client, tecnico):
    """Integración con HU-018: la orden informa cuántos consumos de repuestos tiene."""
    client.post(url(), json=BODY, headers=tecnico)
    assert client.get("/api/v1/ordenes-servicio/OS-0001").json()["data"]["repuestosConsumidos"] == 1


def test_recepcion_no_puede_registrar(client, tecnico):
    assert client.post(url(), json=BODY).status_code == 403  # el client usa el token de recepción


def test_requiere_token(client_sin_token):
    r = client_sin_token.post(url(), json=BODY)
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"
