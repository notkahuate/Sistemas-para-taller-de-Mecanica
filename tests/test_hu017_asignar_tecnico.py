"""Casos de prueba de HU-017 Asignar técnico a la orden (Parcial 2, FUN-17)."""
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
BODY = {"idTecnico": "TEC-0001", "idEspecialidadRequerida": "ESP-FRE", "fechaAsignacion": "2026-10-14T09:00:00-05:00"}
CAMPOS_DATA = {"idOrden", "idTecnico", "nombreTecnico", "idEspecialidadRequerida", "estado", "fechaAsignacion"}
MSG_INVALIDOS = "No fue posible completar «Asignar técnico a la orden»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Asignar técnico a la orden»: la operación viola una regla de negocio."


def url(id_orden="OS-0001"):
    return f"/api/v1/ordenes-servicio/{id_orden}/tecnico"


def _registrar_tecnico(client, documento="109111222", nombre="Luis Martínez"):
    """Los técnicos los registra el administrador (HU-076)."""
    token = iniciar_sesion(client, "admin", "Admin123*")
    r = client.post(
        "/api/v1/tecnicos",
        json={**TECNICO, "numeroDocumento": documento, "nombreCompleto": nombre},
        headers={"Authorization": f"Bearer {token}"},
    )
    return r.json()["data"]["idTecnico"]


def _registrar_orden(client):
    id_cliente = client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]
    id_moto = client.post("/api/v1/motocicletas", json={**MOTO, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    r = client.post(
        "/api/v1/ordenes-servicio",
        json={
            "idCliente": id_cliente,
            "idMotocicleta": id_moto,
            "motivoVisita": "Ruido en frenos",
            "fechaIngreso": "2026-10-14T08:30:00-05:00",
        },
    )
    return r.json()["data"]["idOrden"]


@pytest.fixture
def escenario(client):
    """Orden OS-0001 en estado recibida y técnico TEC-0001 activo."""
    _registrar_orden(client)
    _registrar_tecnico(client)
    return client


def _actualizar(modelo, filtro: dict, cambios: dict):
    from app.core.database import SessionLocal

    with SessionLocal() as db:
        db.query(modelo).filter_by(**filtro).update(cambios)
        db.commit()


def test_caso1_asignacion_exitosa(escenario):
    r = escenario.patch(url(), json=BODY)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Técnico asignado a la orden correctamente"
    assert cuerpo["data"] == {
        "idOrden": "OS-0001",
        "idTecnico": "TEC-0001",
        "nombreTecnico": "Luis Martínez",
        "idEspecialidadRequerida": "ESP-FRE",
        "estado": "en_proceso",
        "fechaAsignacion": "2026-10-14T09:00:00-05:00",
    }


def test_caso2_contrato_json(escenario):
    cuerpo = escenario.patch(url(), json=BODY).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    assert set(cuerpo["data"]) == CAMPOS_DATA


def test_caso3_tecnico_inactivo_rn06(escenario):
    from app.domain.models.tecnico import TecnicoModel

    _actualizar(TecnicoModel, {"id_tecnico": "TEC-0001"}, {"estado": "inactivo"})
    r = escenario.patch(url(), json=BODY)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "RN-06", "detalle": "Técnico inactivo RN-06"}]


def test_caso4_orden_finalizada_rn02(escenario):
    from app.domain.models.orden_servicio import OrdenServicioModel

    _actualizar(OrdenServicioModel, {"id_orden": "OS-0001"}, {"estado": "finalizada"})
    r = escenario.patch(url(), json=BODY)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "RN-02", "detalle": "Orden finalizada RN-02"}]


def test_caso5_fallo_de_base_de_datos(escenario):
    with patch(
        "app.repositories.orden_servicio_repository.OrdenServicioRepository.obtener_por_id",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = escenario.patch(url(), json=BODY)
    assert r.status_code == 503
    assert r.json()["success"] is False
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_la_asignacion_queda_guardada(escenario):
    from app.core.database import SessionLocal
    from app.domain.models.orden_servicio import OrdenServicioModel

    escenario.patch(url(), json=BODY)
    with SessionLocal() as db:
        orden = db.query(OrdenServicioModel).filter_by(id_orden="OS-0001").one()
        assert (orden.id_tecnico, orden.id_especialidad_requerida, orden.estado) == ("TEC-0001", "ESP-FRE", "en_proceso")


def test_reasignar_en_proceso_cambia_el_tecnico(escenario):
    _registrar_tecnico(escenario, documento="109333444", nombre="Ana Rojas")
    escenario.patch(url(), json=BODY)
    r = escenario.patch(url(), json={**BODY, "idTecnico": "TEC-0002"})
    assert r.status_code == 200
    assert r.json()["data"]["idTecnico"] == "TEC-0002"
    assert r.json()["data"]["nombreTecnico"] == "Ana Rojas"


def test_especialidad_es_opcional(escenario):
    r = escenario.patch(url(), json={"idTecnico": "TEC-0001", "fechaAsignacion": "2026-10-14T09:00:00-05:00"})
    assert r.status_code == 200
    assert r.json()["data"]["idEspecialidadRequerida"] is None


def test_orden_inexistente(escenario):
    r = escenario.patch(url("OS-9999"), json=BODY)
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "idOrden"


def test_tecnico_inexistente(escenario):
    r = escenario.patch(url(), json={**BODY, "idTecnico": "TEC-9999"})
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "idTecnico"


@pytest.mark.parametrize(
    "ruta, cambios, campo",
    [
        ("OS-1", {}, "idOrden"),
        ("OS-0001", {"idTecnico": "TEC-12"}, "idTecnico"),
        ("OS-0001", {"idEspecialidadRequerida": "frenos"}, "idEspecialidadRequerida"),
        ("OS-0001", {"fechaAsignacion": "2026-10-14T09:00:00"}, "fechaAsignacion"),
    ],
)
def test_formatos_invalidos(escenario, ruta, cambios, campo):
    r = escenario.patch(url(ruta), json={**BODY, **cambios})
    assert r.status_code == 400
    assert r.json()["message"] == MSG_INVALIDOS
    assert r.json()["errors"][0] == {"campo": campo, "codigo": "VAL-FORMATO", "detalle": r.json()["errors"][0]["detalle"]}


def test_campo_obligatorio_y_campos_extra(escenario):
    assert escenario.patch(url(), json={"idTecnico": "TEC-0001"}).status_code == 400
    assert escenario.patch(url(), json={**BODY, "estado": "finalizada"}).status_code == 400


def test_rol_tecnico_no_puede_asignar(escenario, client_sin_token):
    token = iniciar_sesion(client_sin_token, "tecnico", "Tecnico123*")
    r = client_sin_token.patch(url(), json=BODY, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_administrador_puede_asignar(escenario, client_sin_token):
    token = iniciar_sesion(client_sin_token, "admin", "Admin123*")
    r = client_sin_token.patch(url(), json=BODY, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_requiere_token(client_sin_token):
    r = client_sin_token.patch(url(), json=BODY)
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"
