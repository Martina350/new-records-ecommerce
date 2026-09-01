"""Reglas PostgreSQL específicas de New Records.

Revision ID: b4de1a3ffd48
Revises: 4c760dc0230c
Create Date: 2026-08-31 18:15:21.068363

"""

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "b4de1a3ffd48"
down_revision = "4c760dc0230c"
branch_labels = None
depends_on = None


def _ejecutar_script(nombre):
    raiz = Path(__file__).resolve().parents[2]
    contenido = (raiz / "database" / nombre).read_text(encoding="utf-8")
    conexion_dbapi = op.get_bind().connection
    with conexion_dbapi.cursor() as cursor:
        cursor.execute(contenido)


def upgrade():
    """Instala secuencias, triggers, restricciones y aprobación atómica."""
    _ejecutar_script("rules_codigos_discos.sql")
    _ejecutar_script("rules_fases7_10.sql")
    _ejecutar_script("rules_fases12.sql")


def downgrade():
    """Retira las rutinas; las tablas y CHECK base pertenecen al baseline."""
    op.execute("DROP TRIGGER IF EXISTS trg_discos_actualizar_fecha ON discos")
    op.execute("DROP TRIGGER IF EXISTS trg_metodos_pago_vencimiento ON metodos_pago")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_verificaciones_tarjeta_vencimiento "
        "ON verificaciones_tarjeta"
    )
    op.execute("DROP PROCEDURE IF EXISTS aprobar_pedido_new_records(VARCHAR, INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS generar_codigo_disco(INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS validar_vencimiento_tarjeta()")
    op.execute("DROP FUNCTION IF EXISTS actualizar_timestamp_modificacion()")
