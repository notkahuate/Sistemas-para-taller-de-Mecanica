"""Casos de prueba de HU-016 Registrar orden de servicio (Parcial #2, FUN-16)."""
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from tests.conftest import CAMPOS_ENVELOPE

URL = "/api/v1/ordenes-servicio"
CLIENTE = {
    "tipoDocumento": "CC",
    "numeroDocumento": "1098765432",
    "nombreCompleto": "Carlos Andrés Pérez Gómez",
    "telefono": "3001234567",
    "correo": "carlos.perez@email.com",
    "direccion": "Calle 45 # 12-30, Bucaramanga",
}
MOTO = {"placa": "ABC12D", "vin": None, "marca": "Yamaha", "linea": "FZ 2.0", "anio": 2023, "cilindraje": 150, "color": "Azul"}
CAMPOS_DATA = {
    "idOrden", "idCliente", "idMotocicleta", "idCita", "motivoVisita",
    "estado", "fechaIngreso", "observaciones", "idTecnico",
}
MSG_INVALIDOS = "No fue posible completar «Registrar orden de servicio»: los datos enviados no son válidos."
MSG_REGLA = "No fue posible completar «Registrar orden de servicio»: la operación viola una regla de negocio."


def _cliente_y_moto(client, documento="1098765432", placa="ABC12D"):
    id_cliente = client.post("/api/v1/clientes", json={**CLIENTE, "numeroDocumento": documento}).json()["data"]["idCliente"]
    id_moto = client.post("/api/v1/motocicletas", json={**MOTO, "placa": placa, "idCliente": id_cliente}).json()["data"]["idMotocicleta"]
    return id_cliente, id_moto


def _orden(id_cliente, id_moto, **extra):
    return {
        "idCliente": id_cliente,
        "idMotocicleta": id_moto,
        "motivoVisita": "Mantenimiento 5000 km y ruido en frenos",
        "fechaIngreso": "2026-10-14T08:30:00-05:00",
        "observaciones": "Cliente deja casco en recepción",
        **extra,
    }


def _inactivar(modelo, campo, valor):
    from app.core.database import SessionLocal

    with SessionLocal() as db:
        db.query(modelo).filter_by(**{campo: valor}).update({"estado": "inactivo"})
        db.commit()


def test_caso1_registro_exitoso(client):
    id_cliente, id_moto = _cliente_y_moto(client)
    r = client.post(URL, json=_orden(id_cliente, id_moto))
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Orden de servicio registrada correctamente"
    assert cuerpo["data"] == {
        "idOrden": "OS-0001",
        "idCliente": id_cliente,
        "idMotocicleta": id_moto,
        "idCita": None,
        "motivoVisita": "Mantenimiento 5000 km y ruido en frenos",
        "estado": "recibida",
        "fechaIngreso": "2026-10-14T08:30:00-05:00",
        "observaciones": "Cliente deja casco en recepción",
        "idTecnico": None,
    }


def test_caso2_contrato_json(client):
    cuerpo = client.post(URL, json=_orden(*_cliente_y_moto(client))).json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["errors"] == []
    assert cuerpo["timestamp"].endswith("-05:00")
    assert set(cuerpo["data"]) == CAMPOS_DATA


def test_caso3_cliente_inactivo_rn01(client):
    from app.domain.models.cliente import ClienteModel

    id_cliente, id_moto = _cliente_y_moto(client)
    _inactivar(ClienteModel, "id_cliente", id_cliente)
    r = client.post(URL, json=_orden(id_cliente, id_moto))
    assert r.status_code == 409
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_REGLA
    assert cuerpo["data"] is None
    assert cuerpo["errors"] == [{"campo": "request", "codigo": "RN-01", "detalle": "Cliente o motocicleta inactivos RN-01"}]


def test_caso3_motocicleta_inactiva_rn01(client):
    from app.domain.models.motocicleta import MotocicletaModel

    id_cliente, id_moto = _cliente_y_moto(client)
    _inactivar(MotocicletaModel, "id_motocicleta", id_moto)
    r = client.post(URL, json=_orden(id_cliente, id_moto))
    assert r.status_code == 409
    assert r.json()["errors"][0]["codigo"] == "RN-01"


def test_caso4_motivo_visita_vacio(client):
    r = client.post(URL, json=_orden(*_cliente_y_moto(client), motivoVisita="   "))
    assert r.status_code == 400
    cuerpo = r.json()
    assert cuerpo["message"] == MSG_INVALIDOS
    assert cuerpo["errors"] == [{"campo": "motivoVisita", "codigo": "VAL-REQUERIDO", "detalle": "MotivoVisita vacío"}]


def test_caso5_fallo_de_base_de_datos(client):
    id_cliente, id_moto = _cliente_y_moto(client)
    with patch(
        "app.repositories.orden_servicio_repository.OrdenServicioRepository.tiene_orden_abierta",
        side_effect=OperationalError("SELECT", {}, Exception("BD caída")),
    ):
        r = client.post(URL, json=_orden(id_cliente, id_moto))
    assert r.status_code == 503
    assert r.json()["errors"][0]["codigo"] == "DB-DOWN"


def test_moto_de_otro_cliente_rn01(client):
    id_cliente_1, _ = _cliente_y_moto(client)
    _, id_moto_2 = _cliente_y_moto(client, documento="1098765433", placa="XYZ98A")
    r = client.post(URL, json=_orden(id_cliente_1, id_moto_2))
    assert r.status_code == 409
    assert r.json()["errors"][0] == {
        "campo": "idMotocicleta",
        "codigo": "RN-01",
        "detalle": "La motocicleta no pertenece al cliente indicado RN-01",
    }


def test_cliente_inexistente_404(client):
    _, id_moto = _cliente_y_moto(client)
    r = client.post(URL, json=_orden("CLI-9999", id_moto))
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "idCliente"


def test_motocicleta_inexistente_404(client):
    id_cliente, _ = _cliente_y_moto(client)
    r = client.post(URL, json=_orden(id_cliente, "MTO-9999"))
    assert r.status_code == 404
    assert r.json()["errors"][0]["campo"] == "idMotocicleta"


def test_moto_con_orden_abierta_no_admite_otra(client):
    id_cliente, id_moto = _cliente_y_moto(client)
    client.post(URL, json=_orden(id_cliente, id_moto))
    r = client.post(URL, json=_orden(id_cliente, id_moto))
    assert r.status_code == 409
    assert r.json()["errors"][0]["codigo"] == "ORD-ABIERTA"


def test_formato_de_ids_invalido(client):
    r = client.post(URL, json=_orden("1024", "MTO-1"))
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "idCliente"


def test_cita_no_disponible_en_esta_version(client):
    r = client.post(URL, json=_orden(*_cliente_y_moto(client), idCita="CIT-0880"))
    assert r.status_code == 400
    assert r.json()["errors"][0]["campo"] == "idCita"


def test_observaciones_opcionales(client):
    body = _orden(*_cliente_y_moto(client))
    body.pop("observaciones")
    r = client.post(URL, json=body)
    assert r.status_code == 201
    assert r.json()["data"]["observaciones"] is None


def test_requiere_token(client_sin_token):
    assert client_sin_token.post(URL, json=_orden("CLI-0001", "MTO-0001")).status_code == 401


def test_rol_tecnico_no_puede_registrar(client_sin_token):
    from tests.conftest import iniciar_sesion

    token = iniciar_sesion(client_sin_token, "tecnico", "Tecnico123*")
    r = client_sin_token.post(URL, json=_orden("CLI-0001", "MTO-0001"), headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
