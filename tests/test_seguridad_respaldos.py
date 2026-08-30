"""Pruebas de integridad avanzada, seguridad HTTP y respaldos — Fase 12."""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app import app
from backup_manager import (
    generar_nombre_backup,
    listar_backups_locales,
    obtener_carpeta_backups,
)
from models import CD, Categoria, Disco, Usuario, db


# ── Tests de Seguridad en Capa Web (Cabeceras HTTP) ───────────────────────────

def test_cabeceras_http_seguridad(client):
    """Las respuestas de la aplicación deben incluir cabeceras HTTP de seguridad."""
    respuesta = client.get("/")
    assert respuesta.status_code == 200

    assert respuesta.headers.get("X-Content-Type-Options") == "nosniff"
    assert respuesta.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert respuesta.headers.get("X-XSS-Protection") == "1; mode=block"
    assert (
        respuesta.headers.get("Referrer-Policy")
        == "strict-origin-when-cross-origin"
    )


# ── Tests de Restricciones Relacionales e Integridad en PostgreSQL ────────────

def test_postgresql_rechaza_disco_precio_invalido(client):
    """PostgreSQL debe rechazar discos con precio negativo o cero."""
    with app.app_context():
        cat = Categoria.query.filter_by(activo=True).first()
        with pytest.raises(IntegrityError):
            db.session.execute(
                text(
                    "INSERT INTO discos (categoria_id, codigo, album, artista, descripcion, "
                    "precio_base, stock, peso_kg, costo_envio_por_kg, formato, activo) "
                    "VALUES (:cat, 'NR-TEST-PNEG', 'Album Test', 'Artista Test', 'Desc', "
                    "-10.00, 5, 0.2, 2.0, 'CD', true)"
                ),
                {"cat": cat.id},
            )
            db.session.flush()


def test_postgresql_rechaza_disco_peso_negativo(client):
    """PostgreSQL debe rechazar discos con peso negativo o cero."""
    with app.app_context():
        cat = Categoria.query.filter_by(activo=True).first()
        with pytest.raises(IntegrityError):
            db.session.execute(
                text(
                    "INSERT INTO discos (categoria_id, codigo, album, artista, descripcion, "
                    "precio_base, stock, peso_kg, costo_envio_por_kg, formato, activo) "
                    "VALUES (:cat, 'NR-TEST-WNEG', 'Album Test', 'Artista Test', 'Desc', "
                    "20.00, 5, -0.5, 2.0, 'CD', true)"
                ),
                {"cat": cat.id},
            )
            db.session.flush()


def test_postgresql_rechaza_formato_disco_desconocido(client):
    """PostgreSQL debe restringir los formatos exclusivamente a CD o VINILO."""
    with app.app_context():
        cat = Categoria.query.filter_by(activo=True).first()
        with pytest.raises(IntegrityError):
            db.session.execute(
                text(
                    "INSERT INTO discos (categoria_id, codigo, album, artista, descripcion, "
                    "precio_base, stock, peso_kg, costo_envio_por_kg, formato, activo) "
                    "VALUES (:cat, 'NR-TEST-CAS', 'Album Cassette', 'Artista Test', 'Desc', "
                    "20.00, 5, 0.2, 2.0, 'CASSETTE', true)"
                ),
                {"cat": cat.id},
            )
            db.session.flush()


def test_postgresql_rechaza_rol_invalido(client):
    """PostgreSQL debe restringir los roles a 'cliente' o 'administrador'."""
    with app.app_context():
        with pytest.raises(IntegrityError):
            db.session.execute(
                text(
                    "INSERT INTO usuarios (nombre, email, password_hash, rol, activo) "
                    "VALUES ('Hacker', 'hacker@test.local', 'hash123', 'superadmin', true)"
                )
            )
            db.session.flush()


def test_postgresql_rechaza_pedido_rechazado_sin_motivo(client):
    """Un pedido en estado RECHAZADO debe contener obligatoriamente un motivo_rechazo."""
    with app.app_context():
        cliente = Usuario.query.filter_by(rol="cliente").first()
        with pytest.raises(IntegrityError):
            db.session.execute(
                text(
                    "INSERT INTO pedidos (numero, cliente_id, estado, total, motivo_rechazo) "
                    "VALUES ('NR-TEST-RECH-ERR', :cid, 'RECHAZADO', 0.00, NULL)"
                ),
                {"cid": cliente.id},
            )
            db.session.flush()


# ── Tests de Triggers de Consistencia ─────────────────────────────────────────

def test_trigger_actualiza_fecha_modificacion_disco(client):
    """El trigger trg_discos_actualizar_fecha debe actualizar fecha_actualizacion al modificar un disco."""
    with app.app_context():
        disco = Disco.query.filter_by(activo=True).first()
        fecha_original = disco.fecha_actualizacion

        # Forzar actualización
        db.session.execute(
            text(
                "UPDATE discos SET stock = stock + 1 WHERE id = :id"
            ),
            {"id": disco.id},
        )
        db.session.commit()

        db.session.refresh(disco)
        assert disco.fecha_actualizacion is not None
        if fecha_original is not None:
            assert disco.fecha_actualizacion >= fecha_original


# ── Tests del Gestor de Respaldos y Documentación ─────────────────────────────

def test_backup_manager_generacion_nombres_y_directorios():
    """El gestor de respaldos genera nombres válidos y asegura el directorio local."""
    carpeta = obtener_carpeta_backups()
    assert carpeta.exists()
    assert carpeta.is_dir()

    nombre_sql = generar_nombre_backup("sql")
    assert nombre_sql.startswith("new_records_backup_")
    assert nombre_sql.endswith(".sql")

    nombre_dump = generar_nombre_backup("dump")
    assert nombre_dump.startswith("new_records_backup_")
    assert nombre_dump.endswith(".dump")


def test_script_roles_seguridad_existe_y_declara_roles():
    """El script de roles debe definir new_records_app, new_records_backup y new_records_admin."""
    ruta_roles = Path(__file__).resolve().parent.parent / "database" / "roles_seguridad.sql"
    assert ruta_roles.exists()
    contenido = ruta_roles.read_text(encoding="utf-8")

    assert "new_records_app" in contenido
    assert "new_records_backup" in contenido
    assert "new_records_admin" in contenido
    assert "GRANT SELECT, INSERT, UPDATE, DELETE" in contenido
