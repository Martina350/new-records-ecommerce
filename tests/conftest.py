"""Fixtures compartidas para ejecutar pruebas sin persistir cambios en PostgreSQL."""

import pytest

from app import app
from models import db


@pytest.fixture()
def client(tmp_path):
    """Ejecuta cada prueba web dentro de una transacción reversible."""
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        MAIL_SUPPRESS_SEND=True,
        PDF_OUTPUT_DIR=str(tmp_path / "comprobantes"),
    )

    with app.app_context():
        motores = db.engines
        motor_original = motores[None]
        conexion = motor_original.connect()
        transaccion = conexion.begin()

        db.session.remove()
        motores[None] = conexion
        db.session.configure(join_transaction_mode="create_savepoint")
        assert db.session().get_bind() is conexion

        try:
            yield app.test_client()
        finally:
            db.session.remove()
            if transaccion.is_active:
                transaccion.rollback()
            conexion.close()
            motores[None] = motor_original
            db.session.configure(join_transaction_mode="conditional_savepoint")
