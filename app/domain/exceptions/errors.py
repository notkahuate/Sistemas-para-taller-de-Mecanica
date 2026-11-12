"""Excepciones de la aplicación. El manejador global las convierte en el envelope estándar."""


class AppError(Exception):
    """Error controlado con los datos que van en errors[] y el código HTTP."""

    status_code = 400

    def __init__(self, message: str, codigo: str, detalle: str, campo: str | None = None):
        super().__init__(detalle)
        self.message = message
        self.codigo = codigo
        self.detalle = detalle
        self.campo = campo


class FormatoInvalidoError(AppError):
    """HTTP 400 · VAL-FORMATO: un dato no cumple el formato del contrato."""

    status_code = 400

    def __init__(self, message: str, detalle: str, campo: str):
        super().__init__(message, "VAL-FORMATO", detalle, campo)


class ReglaNegocioError(AppError):
    """HTTP 409 · RN-XX: se incumple una regla de negocio."""

    status_code = 409


class NoEncontradoError(AppError):
    """HTTP 404 · NOT-FOUND: el recurso solicitado no existe."""

    status_code = 404

    def __init__(self, detalle: str, campo: str):
        super().__init__(detalle, "NOT-FOUND", detalle, campo)
