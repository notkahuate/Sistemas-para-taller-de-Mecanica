# Configuración del entorno – <TU NOMBRE>

- Rama: `entorno/<tu-usuario>`
- Sistema operativo: <Windows 11 / Ubuntu / macOS>
- Versión de Python (`python --version`): <pegar>
- Versión de pip (`pip --version`): <pegar>

## Paquetes instalados (`pip list` o `pip freeze`)

```
<pegar aquí>
```

## Verificación

- [ ] Entorno virtual creado y activado (`(venv)` en la terminal)
- [ ] `pip install -r requirements.txt` sin errores
- [ ] `.env` creado a partir de `.env.example`
- [ ] Servidor corriendo con `uvicorn main:app --reload`
- [ ] Swagger UI abre en http://localhost:8000/docs
- [ ] `/health` responde `{"status": "ok", ...}`

Respuesta de /health:

```
<pegar aquí>
```

Captura de Swagger UI: ![swagger](swagger-<tu-usuario>.png)
