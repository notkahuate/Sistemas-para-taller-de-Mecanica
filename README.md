# MotoService API

Web Service para la gestión de un taller de mecánica de motos.
Python 3.10+ · FastAPI · SQLAlchemy · Pydantic v2 · Uvicorn

## Arquitectura por capas

```
app/
├── api/           ← routers, schemas, dependencias (API Layer)
├── domain/        ← modelos, entidades, excepciones, interfaces (Domain Layer)
├── services/      ← lógica de negocio, casos de uso (Service Layer)
├── repositories/  ← acceso a datos (Repository Layer)
└── core/          ← configuración y base de datos
```

## Levantar el entorno

```bash
python -m venv venv
# Windows PowerShell: venv\Scripts\Activate.ps1   |  Linux/macOS: source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env        # en Windows: copy .env.example .env
uvicorn main:app --reload
```

Abrir http://localhost:8000/docs y http://localhost:8000/health

Cada integrante documenta la configuración de su entorno en `docs/entorno/`.

## Autenticación (HT-02)

Todos los endpoints de negocio exigen un token. Para obtenerlo:

1. En Swagger (`/docs`), ejecuta **POST /api/v1/auth/login** con un usuario de prueba.
2. Copia el `accessToken` de la respuesta.
3. Pulsa **Authorize** (arriba a la derecha), pega el token y acepta.

Usuarios que se crean solos la primera vez que arranca la API (solo para desarrollo):

| Usuario | Clave | Rol |
| --- | --- | --- |
| admin | Admin123* | administrador |
| recepcion | Recepcion123* | recepcion |
| tecnico | Tecnico123* | tecnico |
| inventario | Inventario123* | inventario |

Sin token o con token vencido la API responde 401 (`AUTH-401`); con un rol sin permiso, 403 (`AUTH-403`).
