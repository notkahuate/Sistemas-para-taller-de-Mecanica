"""Validaciones de formato de un diagnóstico técnico (FUN-21)."""
from app.domain.entities.diagnostico_tecnico import TEXTO_MAX, TEXTO_MIN
from app.domain.entities.orden_servicio import ID_ORDEN_RE

# campo del body -> nombre en el contrato y detalle cuando el texto no llega a 15 caracteres
TEXTOS = (
    ("hallazgos", "hallazgos", "Hallazgos incompletos"),
    ("pruebas", "pruebas", "Pruebas incompletas"),
    ("diagnostico", "diagnostico", "Diagnóstico incompleto"),
)


def validar_formato_diagnostico(id_orden: str, datos: dict) -> list[tuple[str, str, str]]:
    """Devuelve una lista de (campo, código, detalle) con cada dato que no cumple el contrato."""
    errores: list[tuple[str, str, str]] = []
    if not ID_ORDEN_RE.match(id_orden):
        errores.append(("idOrden", "VAL-FORMATO", "Formato de idOrden no válido. Debe ser OS-NNNN."))
    for clave, campo, incompleto in TEXTOS:
        texto = datos[clave].strip()
        if len(texto) < TEXTO_MIN:
            errores.append((campo, "VAL-FORMATO", incompleto))
        elif len(texto) > TEXTO_MAX:
            errores.append((campo, "VAL-FORMATO", f"{campo} no puede superar {TEXTO_MAX} caracteres."))
    recomendaciones = datos.get("recomendaciones")
    if recomendaciones is not None and len(recomendaciones.strip()) > TEXTO_MAX:
        errores.append(("recomendaciones", "VAL-FORMATO", f"recomendaciones no puede superar {TEXTO_MAX} caracteres."))
    return errores
