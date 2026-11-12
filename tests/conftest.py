"""Configuración compartida de pruebas: base de datos SQLite temporal y cliente HTTP."""
import os
import tempfile

# La base de pruebas se define ANTES de importar la app, para no tocar dev.db.
_carpeta = tempfile.mkdtemp(prefix="motoservice-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_carpeta, 'test.db')}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from main import app  # noqa: E402

CAMPOS_ENVELOPE = {"success", "message", "data", "errors", "timestamp", "traceId"}


@pytest.fixture(autouse=True)
def base_limpia():
    """Cada prueba arranca con las tablas vacías."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def iniciar_sesion(c: TestClient, usuario: str, clave: str) -> str:
    r = c.post("/api/v1/auth/login", json={"usuario": usuario, "clave": clave})
    return r.json()["data"]["accessToken"]


@pytest.fixture
def client():
    """Cliente autenticado como recepción (el rol que usan HU-001 y HU-002)."""
    with TestClient(app) as c:
        c.headers["Authorization"] = f"Bearer {iniciar_sesion(c, 'recepcion', 'Recepcion123*')}"
        yield c


@pytest.fixture
def client_sin_token():
    with TestClient(app) as c:
        yield c
