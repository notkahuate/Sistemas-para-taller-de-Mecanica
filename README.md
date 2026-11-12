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
