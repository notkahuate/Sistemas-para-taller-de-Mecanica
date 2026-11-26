"""Seguridad: hash de claves y tokens JWT (HT-02)."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

ALGORITMO = "HS256"
ITERACIONES = 260_000


def hash_clave(clave: str) -> str:
    """Devuelve la clave cifrada con PBKDF2-SHA256 y una sal aleatoria."""
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), ITERACIONES).hex()
    return f"pbkdf2_sha256${ITERACIONES}${sal}${digest}"


def verificar_clave(clave: str, guardada: str) -> bool:
    try:
        _, iteraciones, sal, digest = guardada.split("$")
    except ValueError:
        return False
    calculado = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), int(iteraciones)).hex()
    return hmac.compare_digest(calculado, digest)


def crear_token(usuario: str, rol: str, minutos: int | None = None) -> str:
    duracion = minutos if minutos is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    ahora = datetime.now(timezone.utc)
    datos = {"sub": usuario, "rol": rol, "iat": ahora, "exp": ahora + timedelta(minutes=duracion)}
    return jwt.encode(datos, settings.SECRET_KEY, algorithm=ALGORITMO)


def decodificar_token(token: str) -> dict:
    """Devuelve los datos del token. Lanza jwt.PyJWTError si es inválido o venció."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITMO])
