"""Casos de prueba de HU-021 Registrar diagnóstico técnico (Parcial 2, FUN-21)."""
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
BODY = {
    "hallazgos": "Pastillas de freno delantero al 20% de vida útil. Aceite oscuro a 5200 km.",
    "pruebas": "Prueba de frenado a 40 km/h; inspección visual de motor.",
    "diagnostico": "Desgaste de pastillas delanteras y aceite vencido por kilometraje.",
    "recomendaciones": "Cambio de pastillas y aceite 10W40. Revisar cadena en próximo servicio.",
}
CAMPOS_DATA = {
    "idDiagnostico", "idOrden", "hallazgos", "pruebas", "diagnostico",
    "recomendaciones", "estado", "idTecnico", "fechaRegistro",
}
MSG_INVALIDOS = "No fue posible completar «Registrar diagnóstico técnico»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar diagnóstico técnico»: la operación viola una regla de negocio."


def url(id_orden="OS-0001"):
    return f"/api/v1/ordenes-servicio/{id_orden}/diagnosticos"


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
            "fechaIngreso": "2026-11-20T08:30:00-05:00",
        },
    )
    client.post("/api/v1/tecnicos", json=TECNICO, headers=_auth(client, "admin", "Admin123*"))


@pytest.fixture
def tecnico(client):
    """Orden OS-0001 en_proceso con TEC-0001 asignado (HU-017); devuelve los headers del usuario tecnico."""
    _orden_recibida(client)
    client.patch(
        "/api/v1/ordenes-servicio/OS-0001/tecnico",
        json={"idTecnico": "TEC-0001", "fechaAsignacion": "2026-11-20T09:00:00-05:00"},
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
    assert cuerpo["message"] == "Diagnóstico técnico registrado correctamente"
    data = cuerpo["data"]
    assert data["fechaRegistro"].endswith("-05:00")
    assert {k: v for k, v in data.items() if k != "fechaRegistro"} == {
        "idDiagnostico": "DG-0001",
        "idOrden": "OS-0001",
        **BODY,
        "estado": "registrado",
        "idTecnico": "TEC-0001",
    }


def test_caso2_contrato_json(client, tecnico):
    cuerpo = client.post(url(), json=BODY, headers=tecnico).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert isinstance(cuerpo["traceId"], str)
    assert set(cuerpo["data"]) == CAMPOS_DATA


@pytest.mark.parametrize("estado", ["finalizada", "recibida"])
def test_caso3_orden_no_esta_en_proceso_rn02(client, tecnico, estado):
    _cambiar_estado_orden(estado)
    r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "RN-02", "detalle": "Orden no está en_proceso"}]


def test_caso3_orden_recibida_sin_tecnico(client):
    _orden_recibida(client)
    r = client.post(url(), json=BODY, headers=_auth(client, "tecnico", "Tecnico123*"))
    assert r.status_code == 409
    assert r.json()["errors"][0]["detalle"] == "Orden no está en_proceso"


@pytest.mark.parametrize("hallazgos", ["", "Pastillas", "   Pastillas    "])
def test_caso4_hallazgos_incompletos(client, tecnico, hallazgos):
    r = client.post(url(), json={**BODY, "hallazgos": hallazgos}, headers=tecnico)
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["errors"] == [{"campo": "hallazgos", "codigo": "VAL-FORMATO", "detalle": "Hallazgos incompletos"}]


def test_caso5_fallo_de_base_de_datos(client, tecnico):
    with patch(
        "app.repositories.diagnostico_tecnico_repository.DiagnosticoTecnicoRepository.crear",
        side_effect=OperationalError("INSERT", {}, Exception("BD caída")),
    ):
        r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 503
    assert r.json()["success"] is False
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_segundo_diagnostico_vigente_responde_409(client, tecnico):
    client.post(url(), json=BODY, headers=tecnico)
    r = client.post(url(), json=BODY, headers=tecnico)
    assert r.status_code == 409
    assert r.json()["errors"][0]["codigo"] == "DIAG-VIGENTE"


@pytest.mark.parametrize(
    "campo, detalle", [("pruebas", "Pruebas incompletas"), ("diagnostico", "Diagnóstico incompleto")]
)
def test_pruebas_y_diagnostico_minimo_15_caracteres(client, tecnico, campo, detalle):
    r = client.post(url(), json={**BODY, campo: "Muy corto"}, headers=tecnico)
    assert r.status_code == 400
    assert r.json()["errors"][0] == {"campo": campo, "codigo": "VAL-FORMATO", "detalle": detalle}


def test_texto_de_exactamente_15_caracteres_es_valido(client, tecnico):
    assert client.post(url(), json={**BODY, "hallazgos": "x" * 15}, headers=tecnico).status_code == 201


def test_recomendaciones_opcionales(client, tecnico):
    cuerpo = {k: v for k, v in BODY.items() if k != "recomendaciones"}
    r = client.post(url(), json=cuerpo, headers=tecnico)
    assert r.status_code == 201
    assert r.json()["data"]["recomendaciones"] is None


def test_textos_muy_largos_e_id_mal_formado(client, tecnico):
    assert client.post(url(), json={**BODY, "hallazgos": "x" * 1001}, headers=tecnico).status_code == 400
    r = client.post(url("OS-1"), json=BODY, headers=tecnico)
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "idOrden"


def test_orden_inexistente(client, tecnico):
    r = client.post(url("OS-9999"), json=BODY, headers=tecnico)
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "idOrden"


def test_campos_obligatorios_y_extra(client, tecnico):
    assert client.post(url(), json={"hallazgos": BODY["hallazgos"]}, headers=tecnico).status_code == 400
    assert client.post(url(), json={**BODY, "estado": "cerrado"}, headers=tecnico).status_code == 400


def test_consulta_de_orden_marca_tiene_diagnostico(client, tecnico):
    """Integración con HU-018: tras registrar el diagnóstico la orden informa tieneDiagnostico=true."""
    assert client.get("/api/v1/ordenes-servicio/OS-0001").json()["data"]["tieneDiagnostico"] is False
    client.post(url(), json=BODY, headers=tecnico)
    assert client.get("/api/v1/ordenes-servicio/OS-0001").json()["data"]["tieneDiagnostico"] is True


def test_administrador_puede_registrar(client, tecnico):
    assert client.post(url(), json=BODY, headers=_auth(client, "admin", "Admin123*")).status_code == 201


def test_recepcion_no_puede_registrar(client, tecnico):
    assert client.post(url(), json=BODY).status_code == 403  # el client usa el token de recepción


def test_requiere_token(client_sin_token):
    r = client_sin_token.post(url(), json=BODY)
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"
