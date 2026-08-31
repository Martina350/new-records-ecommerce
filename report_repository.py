"""Repositorio de consultas analíticas cargadas desde un único archivo SQL."""

import re
from functools import lru_cache
from pathlib import Path

from sqlalchemy import text

from models import db

RUTA_CONSULTAS = Path(__file__).resolve().parent / "database" / "reports.sql"
PATRON_CONSULTA = re.compile(
    r"^--\s*name:\s*(?P<nombre>[a-z0-9_]+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@lru_cache(maxsize=1)
def cargar_consultas() -> dict[str, str]:
    """Lee y separa las consultas marcadas con `-- name:`."""
    contenido = RUTA_CONSULTAS.read_text(encoding="utf-8")
    coincidencias = list(PATRON_CONSULTA.finditer(contenido))
    consultas: dict[str, str] = {}
    for indice, coincidencia in enumerate(coincidencias):
        inicio = coincidencia.end()
        fin = (
            coincidencias[indice + 1].start()
            if indice + 1 < len(coincidencias)
            else len(contenido)
        )
        consultas[coincidencia.group("nombre").lower()] = contenido[inicio:fin].strip()
    return consultas


def ejecutar_consulta(nombre: str, parametros: dict | None = None):
    """Ejecuta una consulta registrada y devuelve filas como mappings."""
    consulta = cargar_consultas().get(nombre)
    if consulta is None:
        raise KeyError(f"No existe la consulta analítica '{nombre}'.")
    return db.session.execute(text(consulta), parametros or {}).mappings().all()
