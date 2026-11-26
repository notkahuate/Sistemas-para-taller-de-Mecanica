"""Casos de prueba de HU-030 Registrar tiempo de mano de obra (Parcial 2, FUN-30)."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from app.core.responses import ahora_bogota
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
ACTIVIDAD = {"nombre": "Cambio de pastillas de freno delanteras", "estado": "en_ejecucion", "horaInicio": "2026-11-20T09:15:00-05:00"}
BODY = {"horaInicio": "2026-11-20T09:15:00-05:00", "horaFin": "2026-11-20T10:00:00-05:00"}
CAMPOS_DATA = {"idActividad", "idOrden", "minutos", "tarifaHoraria", "valorManoObra", "horaInicio", "horaFin"}
MSG_INVALIDOS = "No fue posible completar «Registrar tiempo de mano de obra»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar tiempo de mano de obra»: la operación viola una regla de negocio."


def url(id_actividad="ACT-0001"):
    return f"/api/v1/actividades/{id_actividad}/mano-obra"


def _auth(client, usuario, clave):
    return {"Authorization": f"Bearer {iniciar_sesion(client, usuario, clave)}"}


@pytest.fixture
def tecnico(client):
    """OS-0001 en_proceso con TEC-0001 (tarifa 40.000/h) y la actividad ACT-0001 (HU-026)."""
    id_cliente = client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]
    id_moto = client.post("/api/v1/motocicletas", json={**MOTO, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    client.post(
        "/api/v1/ordenes-servicio",
        json={"idCliente": id_cliente, "idMotocicleta": id_moto, "motivoVisita": "Ruido en frenos", "fechaIngreso": "2026-11-20T08:30:00-05:00"},
    )
    client.post("/api/v1/tecnicos", json=TECNICO, headers=_auth(client, "admin", "Admin123*"))
    client.patch("/api/v1/ordenes-servicio/OS-0001/tecnico", json={"idTecnico": "TEC-0001", "fechaAsignacion": "2026-11-20T09:00:00-05:00"})
    tec = _auth(client, "tecnico", "Tecnico123*")
    client.post("/api/v1/ordenes-servicio/OS-0001/actividades", json=ACTIVIDAD, headers=tec)
    return tec


def _estado_orden(estado):
    from app.core.database import SessionLocal
    from app.domain.models.orden_servicio import OrdenServicioModel

    with SessionLocal() as db:
        db.query(OrdenServicioModel).filter_by(id_orden="OS-0001").update({"estado": estado})
        db.commit()


def test_caso1_registro_exitoso(client, tecnico):
    r = client.patch(url(), json=BODY, headers=tecnico)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Tiempo de mano de obra registrado correctamente"
    assert cuerpo["data"] == {
        "idActividad": "ACT-0001",
        "idOrden": "OS-0001",
        "minutos": 45,
        "tarifaHoraria": 40000.0,
        "valorManoObra": 30000.0,
        "horaInicio": "2026-11-20T09:15:00-05:00",
        "horaFin": "2026-11-20T10:00:00-05:00",
    }


def test_caso2_contrato_json(client, tecnico):
    cuerpo = client.patch(url(), json=BODY, headers=tecnico).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    assert set(cuerpo["data"]) == CAMPOS_DATA


@pytest.mark.parametrize(
    "fin",
    ["2026-11-20T09:19:00-05:00", "2026-11-20T17:16:00-05:00"],  # 4 minutos y 481 minutos
)
def test_caso3_minutos_fuera_de_rango(client, tecnico, fin):
    r = client.patch(url(), json={**BODY, "horaFin": fin}, headers=tecnico)
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "VAL-FORMATO", "detalle": "Minutos fuera de rango"}]


def test_caso4_orden_finalizada(client, tecnico):
    _estado_orden("finalizada")
    r = client.patch(url(), json=BODY, headers=tecnico)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "RN-02", "detalle": "Orden finalizada"}]


def test_caso5_fallo_de_base_de_datos(client, tecnico):
    with patch(
        "app.repositories.actividad_mantenimiento_repository.ActividadMantenimientoRepository.registrar_mano_obra",
        side_effect=OperationalError("UPDATE", {}, Exception("BD caída")),
    ):
        r = client.patch(url(), json=BODY, headers=tecnico)
    assert r.status_code == 503
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


@pytest.mark.parametrize("fin, minutos", [("2026-11-20T09:20:00-05:00", 5), ("2026-11-20T17:15:00-05:00", 480)])
def test_limites_de_5_y_480_minutos(client, tecnico, fin, minutos):
    r = client.patch(url(), json={**BODY, "horaFin": fin}, headers=tecnico)
    assert r.status_code == 200
    assert r.json()["data"]["minutos"] == minutos


def test_valor_se_redondea_a_2_decimales(client, tecnico):
    # 7 minutos a 40.000/h = 4666,666... -> 4666,67
    r = client.patch(url(), json={**BODY, "horaFin": "2026-11-20T09:22:00-05:00"}, headers=tecnico)
    assert r.json()["data"]["valorManoObra"] == 4666.67


def test_queda_guardado_en_la_actividad(client, tecnico):
    from app.core.database import SessionLocal
    from app.domain.models.actividad_mantenimiento import ActividadMantenimientoModel

    client.patch(url(), json=BODY, headers=tecnico)
    with SessionLocal() as db:
        fila = db.query(ActividadMantenimientoModel).filter_by(id_actividad="ACT-0001").one()
        assert (fila.minutos, float(fila.tarifa_horaria), float(fila.valor_mano_obra)) == (45, 40000.0, 30000.0)
        assert fila.hora_fin is not None


def test_se_puede_corregir_el_tiempo(client, tecnico):
    client.patch(url(), json=BODY, headers=tecnico)
    r = client.patch(url(), json={**BODY, "horaFin": "2026-11-20T10:15:00-05:00"}, headers=tecnico)
    assert (r.json()["data"]["minutos"], r.json()["data"]["valorManoObra"]) == (60, 40000.0)


def test_orden_recibida_rn02(client, tecnico):
    _estado_orden("recibida")
    r = client.patch(url(), json=BODY, headers=tecnico)
    assert r.status_code == 409
    assert r.json()["errors"][0]["detalle"] == "Orden no está en_proceso"


def test_actividad_inexistente(client, tecnico):
    r = client.patch(url("ACT-9999"), json=BODY, headers=tecnico)
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "idActividad"


@pytest.mark.parametrize(
    "ruta, cambios, campo",
    [
        ("ACT-1", {}, "idActividad"),
        ("ACT-0001", {"horaFin": "2026-11-20T09:00:00-05:00"}, "horaFin"),  # fin antes del inicio
        ("ACT-0001", {"horaInicio": "2026-11-20T09:15:00"}, "horaInicio"),  # sin offset
    ],
)
def test_formatos_invalidos(client, tecnico, ruta, cambios, campo):
    r = client.patch(url(ruta), json={**BODY, **cambios}, headers=tecnico)
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == campo


def test_hora_fin_futura(client, tecnico):
    inicio = ahora_bogota() + timedelta(minutes=30)
    cuerpo = {"horaInicio": inicio.isoformat(), "horaFin": (inicio + timedelta(minutes=30)).isoformat()}
    r = client.patch(url(), json=cuerpo, headers=tecnico)
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "horaFin"


def test_tarifa_no_se_envia_en_el_body(client, tecnico):
    assert client.patch(url(), json={**BODY, "tarifaHoraria": 1}, headers=tecnico).status_code == 400


def test_recepcion_no_puede_registrar(client, tecnico):
    assert client.patch(url(), json=BODY).status_code == 403  # el client usa el token de recepción


def test_requiere_token(client_sin_token):
    r = client_sin_token.patch(url(), json=BODY)
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"
