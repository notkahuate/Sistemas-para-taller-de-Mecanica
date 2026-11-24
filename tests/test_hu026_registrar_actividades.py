"""Casos de prueba de HU-026 Registrar actividades de mantenimiento (Parcial 2, FUN-26)."""
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
BODY = {
    "nombre": "Cambio de pastillas de freno delanteras",
    "estado": "en_ejecucion",
    "observaciones": "Se utiliza kit original Yamaha",
    "horaInicio": "2026-11-20T09:15:00-05:00",
}
CAMPOS_DATA = {"idActividad", "idOrden", "idTecnico", "nombre", "estado", "horaInicio", "horaFin"}
MSG_INVALIDOS = "No fue posible completar «Registrar actividades de mantenimiento»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar actividades de mantenimiento»: la operación viola una regla de negocio."


def url(id_orden="OS-0001"):
    return f"/api/v1/ordenes-servicio/{id_orden}/actividades"


def _auth(client, usuario, clave):
    return {"Authorization": f"Bearer {iniciar_sesion(client, usuario, clave)}"}


def _orden_recibida(client):
    """Orden OS-0001 en estado recibida (HU-016) y técnico TEC-0001 activo (HU-076)."""
    id_cliente = client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]
    id_moto = client.post("/api/v1/motocicletas", json={**MOTO, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    client.post(
        "/api/v1/ordenes-servicio",
        json={
            "idCliente": id_cliente,
            "idMotocicleta": id_moto,
            "motivoVisita": "Ruido en frenos",
            "fechaIngreso": "2026-11-24T08:30:00-05:00",
        },
    )
    client.post("/api/v1/tecnicos", json=TECNICO, headers=_auth(client, "admin", "Admin123*"))


@pytest.fixture
def tecnico(client):
    """Orden OS-0001 en_proceso con TEC-0001 asignado (HU-017); devuelve los headers del usuario tecnico."""
    _orden_recibida(client)
    client.patch(
        "/api/v1/ordenes-servicio/OS-0001/tecnico",
        json={"idTecnico": "TEC-0001", "fechaAsignacion": "2026-11-24T09:00:00-05:00"},
    )
    return _auth(client, "tecnico", "Tecnico123*")


def _cambiar_estado_orden(estado):
    from app.core.database import SessionLocal
    from app.domain.models.orden_servicio import OrdenServicioModel

    with SessionLocal() as db:
        db.query(OrdenServicioModel).filter_by(id_orden="OS-0001").update({"estado": estado})
        db.commit()


def test_caso1_registro_exitoso(client, tecnico):
    r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Actividad de mantenimiento registrada correctamente"
    assert cuerpo["data"] == {
        "idActividad": "ACT-0001",
        "idOrden": "OS-0001",
        "idTecnico": "TEC-0001",
        "nombre": "Cambio de pastillas de freno delanteras",
        "estado": "en_ejecucion",
        "horaInicio": "2026-11-20T09:15:00-05:00",
        "horaFin": None,
    }


def test_caso2_contrato_json(client, tecnico):
    cuerpo = client.post(url(), json=BODY, headers=tecnico).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    assert set(cuerpo["data"]) == CAMPOS_DATA


def test_caso3_orden_finalizada_rn02(client, tecnico):
    _cambiar_estado_orden("finalizada")
    r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "RN-02", "detalle": "Orden finalizada RN-02"}]


@pytest.mark.parametrize("nombre", ["", "    "])
def test_caso4_nombre_vacio(client, tecnico, nombre):
    r = client.post(url(), json={**BODY, "nombre": nombre}, headers=tecnico)
    assert r.status_code == 400
    assert r.json()["message"] == MSG_INVALIDOS
    assert r.json()["errors"] == [{"campo": "nombre", "codigo": "VAL-REQUERIDO", "detalle": "Nombre vacío"}]


def test_caso5_fallo_de_base_de_datos(client, tecnico):
    with patch(
        "app.repositories.actividad_mantenimiento_repository.ActividadMantenimientoRepository.crear",
        side_effect=OperationalError("INSERT", {}, Exception("BD caída")),
    ):
        r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 503
    assert r.json()["success"] is False
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_orden_recibida_sin_tecnico_rn02(client):
    _orden_recibida(client)
    r = client.post(url(), json=BODY, headers=_auth(client, "tecnico", "Tecnico123*"))
    assert r.status_code == 409
    assert r.json()["errors"][0]["codigo"] == "RN-02"


def test_orden_inexistente(client, tecnico):
    r = client.post(url("OS-9999"), json=BODY, headers=tecnico)
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "idOrden"


def test_varias_actividades_en_la_misma_orden(client, tecnico):
    client.post(url(), json=BODY, headers=tecnico)
    r = client.post(url(), json={**BODY, "nombre": "Ajuste de cadena", "estado": "completada"}, headers=tecnico)
    assert r.status_code == 201
    assert r.json()["data"]["idActividad"] == "ACT-0002"
    assert r.json()["data"]["estado"] == "completada"


def test_la_actividad_queda_guardada_con_observaciones(client, tecnico):
    from app.core.database import SessionLocal
    from app.domain.models.actividad_mantenimiento import ActividadMantenimientoModel

    client.post(url(), json=BODY, headers=tecnico)
    with SessionLocal() as db:
        fila = db.query(ActividadMantenimientoModel).filter_by(id_actividad="ACT-0001").one()
        assert (fila.id_orden, fila.id_tecnico, fila.observaciones) == ("OS-0001", "TEC-0001", BODY["observaciones"])


def test_observaciones_opcionales(client, tecnico):
    cuerpo = {k: v for k, v in BODY.items() if k != "observaciones"}
    assert client.post(url(), json=cuerpo, headers=tecnico).status_code == 201


@pytest.mark.parametrize(
    "ruta, cambios, campo",
    [
        ("OS-1", {}, "idOrden"),
        ("OS-0001", {"nombre": "Ajus"}, "nombre"),
        ("OS-0001", {"nombre": "x" * 201}, "nombre"),
        ("OS-0001", {"estado": "terminada"}, "estado"),
        ("OS-0001", {"horaInicio": "2026-11-20T09:15:00"}, "horaInicio"),
    ],
)
def test_formatos_invalidos(client, tecnico, ruta, cambios, campo):
    r = client.post(url(ruta), json={**BODY, **cambios}, headers=tecnico)
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == campo
    assert r.json()["errors"][0]["codigo"] == "VAL-FORMATO"


def test_hora_inicio_no_puede_ser_futura(client, tecnico):
    futura = (ahora_bogota() + timedelta(hours=1)).isoformat()
    r = client.post(url(), json={**BODY, "horaInicio": futura}, headers=tecnico)
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "horaInicio"


def test_hora_inicio_dentro_de_la_tolerancia_de_10_minutos(client, tecnico):
    cercana = (ahora_bogota() + timedelta(minutes=5)).isoformat()
    assert client.post(url(), json={**BODY, "horaInicio": cercana}, headers=tecnico).status_code == 201


def test_campos_obligatorios_y_extra(client, tecnico):
    assert client.post(url(), json={"nombre": BODY["nombre"]}, headers=tecnico).status_code == 400
    assert client.post(url(), json={**BODY, "idTecnico": "TEC-0002"}, headers=tecnico).status_code == 400


def test_administrador_puede_registrar(client, tecnico):
    r = client.post(url(), json=BODY, headers=_auth(client, "admin", "Admin123*"))
    assert r.status_code == 201


def test_recepcion_no_puede_registrar(client, tecnico):
    r = client.post(url(), json=BODY)  # el client usa el token de recepción
    assert r.status_code == 403


def test_requiere_token(client_sin_token):
    r = client_sin_token.post(url(), json=BODY)
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"
