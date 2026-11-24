"""Casos de prueba de HU-018 Consultar estado de la orden (Parcial 2, FUN-18)."""
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
ACTIVIDAD = {"nombre": "Cambio de pastillas de freno delanteras", "estado": "en_ejecucion", "horaInicio": "2026-11-20T09:15:00-05:00"}
CAMPOS_DATA = {
    "idOrden", "idCliente", "idMotocicleta", "placa", "estado", "idTecnico", "motivoVisita",
    "fechaIngreso", "fechaCierre", "tieneDiagnostico", "actividadesRegistradas", "repuestosConsumidos",
}
URL = "/api/v1/ordenes-servicio/{}"


def _auth(client, usuario, clave):
    return {"Authorization": f"Bearer {iniciar_sesion(client, usuario, clave)}"}


@pytest.fixture
def orden(client):
    """Orden OS-0001 recibida para CLI-0001 / MTO-0001 (placa ABC12D)."""
    id_cliente = client.post("/api/v1/clientes", json=CLIENTE).json()["data"]["idCliente"]
    id_moto = client.post("/api/v1/motocicletas", json={**MOTO, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    client.post(
        "/api/v1/ordenes-servicio",
        json={
            "idCliente": id_cliente,
            "idMotocicleta": id_moto,
            "motivoVisita": "Mantenimiento 5000 km y ruido en frenos",
            "fechaIngreso": "2026-11-20T08:30:00-05:00",
        },
    )
    return client


@pytest.fixture
def orden_en_proceso(orden):
    """La misma orden con TEC-0001 asignado (HU-017) y dos actividades registradas (HU-026)."""
    orden.post("/api/v1/tecnicos", json=TECNICO, headers=_auth(orden, "admin", "Admin123*"))
    orden.patch(
        "/api/v1/ordenes-servicio/OS-0001/tecnico",
        json={"idTecnico": "TEC-0001", "fechaAsignacion": "2026-11-20T09:00:00-05:00"},
    )
    tecnico = _auth(orden, "tecnico", "Tecnico123*")
    orden.post("/api/v1/ordenes-servicio/OS-0001/actividades", json=ACTIVIDAD, headers=tecnico)
    orden.post("/api/v1/ordenes-servicio/OS-0001/actividades", json={**ACTIVIDAD, "nombre": "Ajuste de cadena"}, headers=tecnico)
    return orden


def test_caso1_consulta_exitosa(orden_en_proceso):
    r = orden_en_proceso.get(URL.format("OS-0001"))
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Consulta de orden de servicio exitosa"
    assert cuerpo["data"] == {
        "idOrden": "OS-0001",
        "idCliente": "CLI-0001",
        "idMotocicleta": "MTO-0001",
        "placa": "ABC12D",
        "estado": "en_proceso",
        "idTecnico": "TEC-0001",
        "motivoVisita": "Mantenimiento 5000 km y ruido en frenos",
        "fechaIngreso": "2026-11-20T08:30:00-05:00",
        "fechaCierre": None,
        "tieneDiagnostico": False,
        "actividadesRegistradas": 2,
        "repuestosConsumidos": 0,
    }


def test_caso2_contrato_json(orden_en_proceso):
    cuerpo = orden_en_proceso.get(URL.format("OS-0001")).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    assert set(cuerpo["data"]) == CAMPOS_DATA


def test_caso3_orden_inexistente(orden):
    r = orden.get(URL.format("OS-9999"))
    assert r.status_code == 404
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No fue posible completar «Consultar estado de la orden»: no existe el recurso indicado."
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "idOrden", "codigo": "NOT-FOUND", "detalle": "Orden inexistente"}]


@pytest.mark.parametrize("id_orden", ["2041", "OS-1", "os-0001", "OS-00012"])
def test_caso4_id_mal_formado(orden, id_orden):
    r = orden.get(URL.format(id_orden))
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["message"] == "No fue posible completar «Consultar estado de la orden»: los datos enviados no son válidos."
    assert cuerpo["errors"] == [{"campo": "idOrden", "codigo": "VAL-FORMATO", "detalle": "IdOrden mal formado (debe OS-NNNN)"}]


def test_caso5_fallo_de_base_de_datos(orden):
    with patch(
        "app.repositories.orden_servicio_repository.OrdenServicioRepository.obtener_por_id",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = orden.get(URL.format("OS-0001"))
    assert r.status_code == 503
    assert r.json()["success"] is False
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_orden_recibida_sin_tecnico_ni_actividades(orden):
    data = orden.get(URL.format("OS-0001")).json()["data"]
    assert (data["estado"], data["idTecnico"], data["actividadesRegistradas"]) == ("recibida", None, 0)


def test_orden_finalizada_tambien_se_consulta(orden):
    from app.core.database import SessionLocal
    from app.domain.models.orden_servicio import OrdenServicioModel

    with SessionLocal() as db:
        db.query(OrdenServicioModel).filter_by(id_orden="OS-0001").update({"estado": "finalizada"})
        db.commit()
    r = orden.get(URL.format("OS-0001"))
    assert r.status_code == 200
    assert r.json()["data"]["estado"] == "finalizada"


@pytest.mark.parametrize("usuario, clave", [("tecnico", "Tecnico123*"), ("admin", "Admin123*")])
def test_tecnico_y_administrador_pueden_consultar(orden, client_sin_token, usuario, clave):
    r = client_sin_token.get(URL.format("OS-0001"), headers=_auth(client_sin_token, usuario, clave))
    assert r.status_code == 200


def test_inventario_no_puede_consultar(orden, client_sin_token):
    r = client_sin_token.get(URL.format("OS-0001"), headers=_auth(client_sin_token, "inventario", "Inventario123*"))
    assert r.status_code == 403


def test_requiere_token(client_sin_token):
    r = client_sin_token.get(URL.format("OS-0001"))
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"
