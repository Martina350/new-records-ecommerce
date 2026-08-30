"""Módulo utilitario para la gestión y ejecución de respaldos de base de datos."""

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from config import Config

RUTA_BACKUPS = Path(__file__).resolve().parent / "backups"


def obtener_carpeta_backups() -> Path:
    """Asegura la existencia del directorio local de respaldos y lo retorna."""
    RUTA_BACKUPS.mkdir(parents=True, exist_ok=True)
    return RUTA_BACKUPS


def generar_nombre_backup(extension: str = "sql") -> str:
    """Genera un nombre descriptivo con timestamp UTC para el archivo de respaldo."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"new_records_backup_{timestamp}.{extension.lstrip('.')}"


def buscar_ejecutable_pg_dump() -> str | None:
    """Busca el ejecutable pg_dump en el PATH del sistema o rutas conocidas en Windows."""
    ruta_en_path = shutil.which("pg_dump")
    if ruta_en_path:
        return ruta_en_path

    # Búsqueda en rutas estándar de PostgreSQL en Windows
    rutas_comunes = [
        r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
    ]
    for ruta in rutas_comunes:
        if os.path.isfile(ruta):
            return ruta

    return None


def ejecutar_backup_pg_dump(formato: str = "plain") -> tuple[bool, str, int]:
    """Genera un respaldo formal de PostgreSQL utilizando pg_dump.
    
    formato: 'plain' (.sql) o 'custom' (.dump).
    Retorna (éxito, ruta_o_mensaje, tamaño_bytes).
    """
    carpeta = obtener_carpeta_backups()
    extension = "sql" if formato == "plain" else "dump"
    nombre_archivo = generar_nombre_backup(extension)
    ruta_destino = carpeta / nombre_archivo

    pg_dump_bin = buscar_ejecutable_pg_dump()
    if not pg_dump_bin:
        return False, "No se encontró el ejecutable pg_dump en el sistema.", 0

    env_dump = os.environ.copy()
    if Config.DB_PASSWORD:
        env_dump["PGPASSWORD"] = Config.DB_PASSWORD

    comando = [
        pg_dump_bin,
        "-h", Config.DB_HOST,
        "-p", str(Config.DB_PORT),
        "-U", Config.DB_USER,
        "-d", Config.DB_NAME,
        "-F", "p" if formato == "plain" else "c",
        "-f", str(ruta_destino),
    ]

    try:
        resultado = subprocess.run(
            comando,
            env=env_dump,
            capture_output=True,
            text=True,
            check=False,
        )

        if resultado.returncode == 0 and ruta_destino.exists():
            tamano = ruta_destino.stat().st_size
            return True, str(ruta_destino), tamano
        else:
            error = resultado.stderr or "Error desconocido al ejecutar pg_dump."
            return False, error.strip(), 0
    except Exception as exc:
        return False, str(exc), 0


def listar_backups_locales() -> list[dict]:
    """Retorna los metadatos de los respaldos disponibles en la carpeta local."""
    carpeta = obtener_carpeta_backups()
    archivos = []
    for elem in sorted(carpeta.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if elem.is_file() and elem.name != ".gitkeep":
            archivos.append(
                {
                    "nombre": elem.name,
                    "ruta": str(elem),
                    "tamano_bytes": elem.stat().st_size,
                    "tamano_kb": round(elem.stat().st_size / 1024, 2),
                    "fecha_creacion": datetime.fromtimestamp(
                        elem.stat().st_mtime, timezone.utc
                    ),
                    "formato": elem.suffix.lstrip(".").upper(),
                }
            )
    return archivos
