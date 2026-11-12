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


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
