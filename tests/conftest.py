"""Fixtures compartidas para ejecutar pruebas sin persistir cambios en PostgreSQL."""

import pytest

from app import app
from models import db


@pytest.fixture()
def client():
    """Ejecuta cada prueba web dentro de una transacción reversible."""
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        conexion = db.engine.connect()
        transaccion = conexion.begin()
        bind_original = db.session.session_factory.kw.get("bind")

        db.session.remove()
        db.session.configure(bind=conexion)

        try:
            yield app.test_client()
        finally:
            db.session.remove()
            if transaccion.is_active:
                transaccion.rollback()
            conexion.close()
            db.session.configure(bind=bind_original)
