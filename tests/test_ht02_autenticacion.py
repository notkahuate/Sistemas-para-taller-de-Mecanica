"""Pruebas de HT-02 Autenticación con roles."""
from app.core.security import crear_token
from tests.conftest import CAMPOS_ENVELOPE, iniciar_sesion

LOGIN = "/api/v1/auth/login"
CLIENTES = "/api/v1/clientes"
BODY_CLIENTE = {
    "tipoDocumento": "CC",
    "numeroDocumento": "1098765432",
    "nombreCompleto": "Carlos Andrés Pérez Gómez",
    "telefono": "3001234567",
    "correo": "carlos.perez@email.com",
    "direccion": "Calle 45 # 12-30, Bucaramanga",
}


def test_login_exitoso_devuelve_token(client_sin_token):
    r = client_sin_token.post(LOGIN, json={"usuario": "recepcion", "clave": "Recepcion123*"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert set(cuerpo) == CAMPOS_ENVELOPE
    assert cuerpo["message"] == "Inicio de sesión exitoso"
    assert cuerpo["data"]["tokenType"] == "bearer"
    assert cuerpo["data"]["rol"] == "recepcion"
    assert cuerpo["data"]["accessToken"]


def test_login_con_clave_incorrecta(client_sin_token):
    r = client_sin_token.post(LOGIN, json={"usuario": "recepcion", "clave": "mala"})
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-CREDENCIALES"


def test_login_usuario_inexistente(client_sin_token):
    r = client_sin_token.post(LOGIN, json={"usuario": "nadie", "clave": "x"})
    assert r.status_code == 401


def test_sin_token_responde_401(client_sin_token):
    r = client_sin_token.get(f"{CLIENTES}/CLI-0001")
    assert r.status_code == 401
    cuerpo = r.json()
    assert cuerpo["success"] is False
    assert cuerpo["message"] == "No autorizado."
    assert cuerpo["errors"][0]["codigo"] == "AUTH-401"


def test_token_invalido_responde_401(client_sin_token):
    r = client_sin_token.get(f"{CLIENTES}/CLI-0001", headers={"Authorization": "Bearer token-falso"})
    assert r.status_code == 401
    assert r.json()["errors"][0]["codigo"] == "AUTH-401"


def test_token_vencido_responde_401(client_sin_token):
    vencido = crear_token("recepcion", "recepcion", minutos=-1)
    r = client_sin_token.get(f"{CLIENTES}/CLI-0001", headers={"Authorization": f"Bearer {vencido}"})
    assert r.status_code == 401


def test_rol_sin_permiso_responde_403(client_sin_token):
    token = iniciar_sesion(client_sin_token, "tecnico", "Tecnico123*")
    r = client_sin_token.post(CLIENTES, json=BODY_CLIENTE, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["errors"][0]["codigo"] == "AUTH-403"


def test_administrador_puede_registrar_cliente(client_sin_token):
    token = iniciar_sesion(client_sin_token, "admin", "Admin123*")
    r = client_sin_token.post(CLIENTES, json=BODY_CLIENTE, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201


def test_health_no_requiere_token(client_sin_token):
    assert client_sin_token.get("/health").status_code == 200
