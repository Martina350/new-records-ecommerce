"""Pruebas de integridad avanzada, seguridad HTTP y respaldos — Fase 12."""

import os
import re
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import app
from backup_manager import (
    generar_nombre_backup,
    obtener_carpeta_backups,
    verificar_restauracion_completa,
)
from models import Categoria, Disco, Usuario, db

# ── Tests de Seguridad en Capa Web (Cabeceras HTTP) ───────────────────────────


def test_cabeceras_http_seguridad(client):
    """Las respuestas de la aplicación deben incluir cabeceras HTTP de seguridad."""
    respuesta = client.get("/")
    assert respuesta.status_code == 200

    assert respuesta.headers.get("X-Content-Type-Options") == "nosniff"
    assert respuesta.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert respuesta.headers.get("X-XSS-Protection") == "1; mode=block"
    assert respuesta.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_csrf_protege_formularios_post(client):
    """Un POST sin token se rechaza y un token emitido por Flask se acepta."""
    estado_original = app.config["WTF_CSRF_ENABLED"]
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        pagina = client.get("/login")
        token = re.search(rb'name="csrf_token" value="([^"]+)"', pagina.data)
        assert token is not None

        sin_token = client.post(
            "/login", data={"email": "nadie@example.com", "password": "x"}
        )
        assert sin_token.status_code == 302

        con_token = client.post(
            "/login",
            data={
                "csrf_token": token.group(1).decode(),
                "email": "nadie@example.com",
                "password": "Password123!",
            },
        )
        assert con_token.status_code == 200
    finally:
        app.config["WTF_CSRF_ENABLED"] = estado_original


def test_configuracion_segura_de_sesion_y_logout(client):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert client.get("/logout").status_code == 405


def test_todos_los_formularios_post_declaran_token_csrf():
    raiz = Path(__file__).resolve().parent.parent / "templates"
    formularios_sin_token = []
    patron = re.compile(
        r"<form\b[^>]*method=[\"']post[\"'][^>]*>(.*?)</form>",
        re.IGNORECASE | re.DOTALL,
    )
    for plantilla in raiz.rglob("*.html"):
        contenido = plantilla.read_text(encoding="utf-8")
        for formulario in patron.findall(contenido):
            if "csrf_token" not in formulario:
                formularios_sin_token.append(str(plantilla.relative_to(raiz)))
    assert formularios_sin_token == []


def test_plantillas_no_exponen_tecnologia_o_logica_interna():
    """El HTML entregado debe utilizar únicamente lenguaje funcional y comercial."""
    raiz = Path(__file__).resolve().parent.parent / "templates"
    terminos_prohibidos = (
        "postgres",
        "sqlalchemy",
        "python",
        "flask",
        "jinja",
        "herencia",
        "polimorf",
        "transaccional",
        "procedimiento almacenado",
        "trigger",
        "backend",
        "frontend",
        "base de datos",
        "smtp",
        "modo desarrollo",
        "cobro simulado",
        "slug url",
        "ruta de imagen",
        "ruta de portada",
    )
    coincidencias = []

    for plantilla in raiz.rglob("*.html"):
        contenido = plantilla.read_text(encoding="utf-8").lower()
        for termino in terminos_prohibidos:
            if termino in contenido:
                coincidencias.append(f"{plantilla.relative_to(raiz)}: {termino}")

    assert coincidencias == []


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
            text("UPDATE discos SET stock = stock + 1 WHERE id = :id"),
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
    ruta_roles = (
        Path(__file__).resolve().parent.parent / "database" / "roles_seguridad.sql"
    )
    assert ruta_roles.exists()
    contenido = ruta_roles.read_text(encoding="utf-8")

    assert "new_records_app" in contenido
    assert "new_records_backup" in contenido
    assert "new_records_admin" in contenido
    assert "GRANT SELECT, INSERT, UPDATE, DELETE" in contenido
    assert "OWNER TO new_records_admin" in contenido
    assert "configurar_en_env" not in contenido
    assert "PASSWORD '" not in contenido


@pytest.mark.skipif(
    os.getenv("RUN_DB_SECURITY_TESTS") != "1",
    reason="Requiere roles PostgreSQL configurados con privilegios reales.",
)
def test_roles_postgresql_aplicados_y_con_minimo_privilegio(client):
    """Auditoría de integración opt-in sobre los roles instalados."""
    with app.app_context():
        roles = {
            fila.rolname: fila
            for fila in db.session.execute(
                text(
                    "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole "
                    "FROM pg_roles WHERE rolname IN "
                    "('new_records_app', 'new_records_backup', 'new_records_admin')"
                )
            ).mappings()
        }
        assert set(roles) == {
            "new_records_app",
            "new_records_backup",
            "new_records_admin",
        }
        assert not roles["new_records_app"].rolsuper
        assert not roles["new_records_app"].rolcreatedb
        assert not roles["new_records_backup"].rolsuper

        propietarios = (
            db.session.execute(
                text(
                    "SELECT DISTINCT tableowner FROM pg_tables WHERE schemaname = 'public'"
                )
            )
            .scalars()
            .all()
        )
        assert set(propietarios) == {"new_records_admin"}
        assert db.session.execute(
            text("SELECT has_table_privilege('new_records_backup', 'discos', 'SELECT')")
        ).scalar_one()
        assert not db.session.execute(
            text("SELECT has_table_privilege('new_records_backup', 'discos', 'UPDATE')")
        ).scalar_one()


@pytest.mark.skipif(
    os.getenv("RUN_DB_RESTORE_TEST") != "1",
    reason="Crea y elimina una base temporal; requiere herramientas y rol administrador.",
)
def test_restauracion_completa_real():
    exito, mensaje, resumen = verificar_restauracion_completa()
    assert exito, mensaje
    assert resumen["tablas"] >= 9
    assert resumen["categorias"] >= 1
    assert resumen["discos"] >= 1
