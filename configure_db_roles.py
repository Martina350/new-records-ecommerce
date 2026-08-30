"""Configura los roles técnicos de PostgreSQL sin guardar contraseñas en SQL."""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql


load_dotenv()

ROLES_ESPERADOS = {
    "DB_USER": "new_records_app",
    "DB_ADMIN_USER": "new_records_admin",
    "DB_BACKUP_USER": "new_records_backup",
}
RUTA_ROLES = Path(__file__).resolve().parent / "database" / "roles_seguridad.sql"


def variable_obligatoria(nombre):
    valor = os.getenv(nombre, "").strip()
    if not valor or valor.startswith("change_"):
        raise RuntimeError(f"Configura {nombre} en .env antes de continuar.")
    return valor


def validar_nombres_roles():
    for variable, esperado in ROLES_ESPERADOS.items():
        actual = os.getenv(variable, esperado).strip()
        if actual != esperado:
            raise RuntimeError(f"{variable} debe ser {esperado} para aplicar la política definida.")


def configurar_roles():
    """Crea roles, rota sus claves y aplica permisos idempotentes."""
    validar_nombres_roles()
    bootstrap_user = variable_obligatoria("DB_BOOTSTRAP_USER")
    bootstrap_password = variable_obligatoria("DB_BOOTSTRAP_PASSWORD")
    claves = {
        "new_records_app": variable_obligatoria("DB_PASSWORD"),
        "new_records_admin": variable_obligatoria("DB_ADMIN_PASSWORD"),
        "new_records_backup": variable_obligatoria("DB_BACKUP_PASSWORD"),
    }

    conexion = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "new_records_db"),
        user=bootstrap_user,
        password=bootstrap_password,
    )
    try:
        with conexion.cursor() as cursor:
            cursor.execute(RUTA_ROLES.read_text(encoding="utf-8"))
            for rol, clave in claves.items():
                atributo_createdb = "CREATEDB" if rol == "new_records_admin" else "NOCREATEDB"
                consulta = sql.SQL(
                    "ALTER ROLE {} WITH LOGIN NOSUPERUSER NOCREATEROLE {} PASSWORD {}"
                ).format(
                    sql.Identifier(rol),
                    sql.SQL(atributo_createdb),
                    sql.Literal(clave),
                )
                cursor.execute(consulta)
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

    print("Roles PostgreSQL configurados correctamente.")
    print("Aplicación, respaldos y administración usan cuentas separadas.")


if __name__ == "__main__":
    configurar_roles()
