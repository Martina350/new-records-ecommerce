"""Validadores compartidos por las rutas web de New Records."""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from email_validator import validate_email
from flask import request


def es_url_segura(destino: str | None, host_url: str | None = None) -> bool:
    """Acepta únicamente redirecciones internas al mismo host de la solicitud."""
    if not destino:
        return False
    host_referencia = urlsplit(host_url or request.host_url).netloc
    host_destino = urlsplit(destino).netloc
    return not host_destino or host_destino == host_referencia


def normalizar_email(email: str) -> str:
    """Valida la estructura y devuelve el correo normalizado en minúsculas."""
    resultado = validate_email(email, check_deliverability=False)
    return resultado.normalized.strip().lower()


def es_solicitud_ajax() -> bool:
    """Detecta los envíos de formularios que esperan una respuesta JSON."""
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.headers.get("Accept", "").startswith("application/json")
        or request.is_json
    )


def slugificar(texto: str) -> str:
    """Genera un identificador URL básico y estable a partir de un nombre."""
    slug = re.sub(r"[^\w\s-]", "", texto.lower()).strip()
    return re.sub(r"[-\s]+", "-", slug)


def prefijo_categoria_valido(prefijo: str) -> bool:
    """Valida el prefijo alfanumérico utilizado en códigos de discos."""
    return re.fullmatch(r"[A-Z0-9]{3,5}", prefijo) is not None


def validar_textos_disco(
    *, formato: str, album: str, artista: str, descripcion: str
) -> list[str]:
    """Replica en el backend las longitudes y campos obligatorios del catálogo."""
    errores: list[str] = []
    if formato not in {"CD", "VINILO"}:
        errores.append("Selecciona un formato válido (CD o VINILO).")
    if not album or len(album) > 150:
        errores.append("El álbum es obligatorio y admite máximo 150 caracteres.")
    if not artista or len(artista) > 120:
        errores.append("El artista es obligatorio y admite máximo 120 caracteres.")
    if not descripcion:
        errores.append("La descripción del álbum es obligatoria.")
    return errores


def validar_nombre_categoria(nombre: str) -> str | None:
    """Devuelve un mensaje cuando el nombre no satisface el dominio."""
    if not 2 <= len(nombre) <= 80:
        return "El nombre de la categoría debe contener entre 2 y 80 caracteres."
    return None


def validar_nombre_persona(nombre: str) -> str | None:
    """Valida el nombre utilizado por cuentas y perfiles."""
    if not nombre:
        return "El nombre completo es un campo obligatorio."
    if not 2 <= len(nombre) <= 100:
        return "El nombre debe contener entre 2 y 100 caracteres."
    return None


def validar_titular_tarjeta(titular: str) -> str | None:
    """Valida el nombre impreso en la tarjeta simulada."""
    if not 3 <= len(titular) <= 120:
        return "El titular debe contener entre 3 y 120 caracteres."
    return None


@dataclass(frozen=True)
class ValoresNumericosDisco:
    """Valores numéricos convertidos y validados de un formulario de disco."""

    precio_base: Decimal
    stock: int
    peso_kg: Decimal
    costo_envio_por_kg: Decimal
    costo_embalaje: Decimal
    categoria_id: int


def convertir_valores_disco(
    *,
    precio_base: str,
    stock: str,
    peso_kg: str,
    costo_envio_por_kg: str,
    costo_embalaje: str,
    categoria_id: str | None,
) -> ValoresNumericosDisco | None:
    """Convierte números del formulario y rechaza valores fuera del dominio."""
    try:
        valores = ValoresNumericosDisco(
            precio_base=Decimal(precio_base),
            stock=int(stock),
            peso_kg=Decimal(peso_kg),
            costo_envio_por_kg=Decimal(costo_envio_por_kg),
            costo_embalaje=Decimal(costo_embalaje),
            categoria_id=int(categoria_id or ""),
        )
    except (InvalidOperation, TypeError, ValueError):
        return None

    if (
        valores.precio_base <= 0
        or valores.stock < 0
        or valores.peso_kg <= 0
        or valores.costo_envio_por_kg < 0
        or valores.costo_embalaje < 0
    ):
        return None
    return valores
