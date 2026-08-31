"""Respaldos y verificación segura de restauraciones PostgreSQL."""

import os
import re
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import psycopg2

from config import Config

RUTA_BACKUPS = Path(__file__).resolve().parent / "backups"
PREFIJO_DB_PRUEBA = "new_records_restore_check_"


def obtener_carpeta_backups() -> Path:
    """Asegura la existencia del directorio local de respaldos y lo retorna."""
    RUTA_BACKUPS.mkdir(parents=True, exist_ok=True)
    return RUTA_BACKUPS


def generar_nombre_backup(extension: str = "sql") -> str:
    """Genera un nombre descriptivo con timestamp UTC para el respaldo."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    return f"new_records_backup_{timestamp}.{extension.lstrip('.')}"


def _directorios_postgresql_windows():
    """Obtiene instalaciones registradas de PostgreSQL en Windows."""
    if os.name != "nt":
        return []
    try:
        import winreg

        rutas = []
        clave_base = r"SOFTWARE\PostgreSQL\Installations"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clave_base) as instalaciones:
            indice = 0
            while True:
                try:
                    nombre = winreg.EnumKey(instalaciones, indice)
                except OSError:
                    break
                with winreg.OpenKey(instalaciones, nombre) as instalacion:
                    base, _ = winreg.QueryValueEx(instalacion, "Base Directory")
                    rutas.append(Path(base) / "bin")
                indice += 1
        return rutas
    except (OSError, ImportError):
        return []


def buscar_ejecutable_postgresql(nombre: str) -> str | None:
    """Busca una herramienta en POSTGRES_BIN, PATH, registro y rutas comunes."""
    ejecutable = f"{nombre}.exe" if os.name == "nt" else nombre
    candidatos = []
    if Config.POSTGRES_BIN:
        candidatos.append(Path(Config.POSTGRES_BIN) / ejecutable)

    ruta_path = shutil.which(nombre)
    if ruta_path:
        return ruta_path

    candidatos.extend(ruta / ejecutable for ruta in _directorios_postgresql_windows())
    if os.name == "nt":
        for version in ("18", "17", "16", "15"):
            candidatos.append(
                Path(rf"C:\Program Files\PostgreSQL\{version}\bin") / ejecutable
            )

    for candidato in candidatos:
        if candidato.is_file():
            return str(candidato)
    return None


def buscar_ejecutable_pg_dump() -> str | None:
    """Compatibilidad con la interfaz utilizada por fases anteriores."""
    return buscar_ejecutable_postgresql("pg_dump")


def _entorno_password(password: str):
    entorno = os.environ.copy()
    entorno["PGPASSWORD"] = password
    return entorno


def ejecutar_backup_pg_dump(
    formato: str = "plain", directorio: Path | None = None
) -> tuple[bool, str, int]:
    """Genera un respaldo con el rol de solo lectura configurado."""
    if formato not in {"plain", "custom"}:
        return False, "El formato debe ser 'plain' o 'custom'.", 0
    if not Config.DB_BACKUP_PASSWORD:
        return False, "Configura DB_BACKUP_PASSWORD antes de generar respaldos.", 0

    carpeta = Path(directorio) if directorio else obtener_carpeta_backups()
    carpeta.mkdir(parents=True, exist_ok=True)
    extension = "sql" if formato == "plain" else "dump"
    ruta_destino = carpeta / generar_nombre_backup(extension)

    pg_dump_bin = buscar_ejecutable_postgresql("pg_dump")
    if not pg_dump_bin:
        return False, "No se encontró pg_dump. Configura POSTGRES_BIN.", 0

    comando = [
        pg_dump_bin,
        "-h",
        Config.DB_HOST,
        "-p",
        str(Config.DB_PORT),
        "-U",
        Config.DB_BACKUP_USER,
        "-d",
        Config.DB_NAME,
        "-F",
        "p" if formato == "plain" else "c",
        "--no-owner",
        "--no-privileges",
        "-f",
        str(ruta_destino),
    ]

    try:
        resultado = subprocess.run(
            comando,
            env=_entorno_password(Config.DB_BACKUP_PASSWORD),
            capture_output=True,
            text=True,
            check=False,
        )
        if resultado.returncode == 0 and ruta_destino.is_file():
            tamano = ruta_destino.stat().st_size
            return True, str(ruta_destino), tamano
        ruta_destino.unlink(missing_ok=True)
        return False, (resultado.stderr or "Error al ejecutar pg_dump.").strip(), 0
    except OSError as exc:
        ruta_destino.unlink(missing_ok=True)
        return False, str(exc), 0


def verificar_restauracion_completa() -> tuple[bool, str, dict]:
    """Restaura un dump en una base temporal, valida el esquema y la elimina."""
    if not Config.DB_ADMIN_PASSWORD or not Config.DB_BACKUP_PASSWORD:
        return False, "Configura las credenciales de administración y respaldo.", {}

    herramientas = {
        nombre: buscar_ejecutable_postgresql(nombre)
        for nombre in ("createdb", "dropdb", "pg_restore")
    }
    faltantes = [nombre for nombre, ruta in herramientas.items() if not ruta]
    if faltantes:
        return False, f"No se encontraron herramientas: {', '.join(faltantes)}.", {}

    db_temporal = f"{PREFIJO_DB_PRUEBA}{uuid4().hex[:10]}"
    if not re.fullmatch(r"new_records_restore_check_[a-f0-9]{10}", db_temporal):
        return False, "No se pudo generar un destino temporal seguro.", {}

    entorno_admin = _entorno_password(Config.DB_ADMIN_PASSWORD)
    base_comando = [
        "-h",
        Config.DB_HOST,
        "-p",
        str(Config.DB_PORT),
        "-U",
        Config.DB_ADMIN_USER,
    ]
    creada = False

    try:
        with tempfile.TemporaryDirectory(prefix="new_records_restore_") as temporal:
            exito, ruta_dump, _ = ejecutar_backup_pg_dump("custom", Path(temporal))
            if not exito:
                return (
                    False,
                    f"No se pudo crear el dump de verificación: {ruta_dump}",
                    {},
                )

            crear = subprocess.run(
                [
                    herramientas["createdb"],
                    *base_comando,
                    "--maintenance-db=postgres",
                    db_temporal,
                ],
                env=entorno_admin,
                capture_output=True,
                text=True,
                check=False,
            )
            if crear.returncode != 0:
                return (
                    False,
                    (crear.stderr or "No se pudo crear la base temporal.").strip(),
                    {},
                )
            creada = True

            restaurar = subprocess.run(
                [
                    herramientas["pg_restore"],
                    *base_comando,
                    "--dbname",
                    db_temporal,
                    "--exit-on-error",
                    "--no-owner",
                    "--no-privileges",
                    ruta_dump,
                ],
                env=entorno_admin,
                capture_output=True,
                text=True,
                check=False,
            )
            if restaurar.returncode != 0:
                return False, (restaurar.stderr or "Falló pg_restore.").strip(), {}

            conexion = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                dbname=db_temporal,
                user=Config.DB_ADMIN_USER,
                password=Config.DB_ADMIN_PASSWORD,
            )
            try:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        "SELECT count(*) FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
                    )
                    tablas = cursor.fetchone()[0]
                    cursor.execute("SELECT count(*) FROM categorias")
                    categorias = cursor.fetchone()[0]
                    cursor.execute("SELECT count(*) FROM discos")
                    discos = cursor.fetchone()[0]
            finally:
                conexion.close()

            if tablas < 9 or categorias < 1 or discos < 1:
                return (
                    False,
                    "La restauración no contiene el esquema o los datos mínimos.",
                    {},
                )
            return (
                True,
                "Restauración completa verificada correctamente.",
                {
                    "tablas": tablas,
                    "categorias": categorias,
                    "discos": discos,
                },
            )
    finally:
        if creada:
            subprocess.run(
                [
                    herramientas["dropdb"],
                    *base_comando,
                    "--maintenance-db=postgres",
                    "--if-exists",
                    db_temporal,
                ],
                env=entorno_admin,
                capture_output=True,
                text=True,
                check=False,
            )


def listar_backups_locales() -> list[dict]:
    """Retorna metadatos de respaldos disponibles en la carpeta local."""
    carpeta = obtener_carpeta_backups()
    archivos = []
    for elem in sorted(
        carpeta.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
    ):
        if elem.is_file() and elem.name != ".gitkeep":
            archivos.append(
                {
                    "nombre": elem.name,
                    "ruta": str(elem),
                    "tamano_bytes": elem.stat().st_size,
                    "tamano_kb": round(elem.stat().st_size / 1024, 2),
                    "fecha_creacion": datetime.fromtimestamp(elem.stat().st_mtime, UTC),
                    "formato": elem.suffix.lstrip(".").upper(),
                }
            )
    return archivos
