"""Pruebas del modelo relacional y polimórfico de la Fase 3."""

from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app import app
from models import CD, Categoria, Disco, Usuario, Vinilo, db


def test_password_se_guarda_como_hash():
    usuario = Usuario(nombre="Prueba", email="prueba@example.com", rol="cliente")

    usuario.set_password("PasswordLocal123!")

    assert usuario.password_hash != "PasswordLocal123!"
    assert usuario.check_password("PasswordLocal123!")
    assert not usuario.check_password("otra-clave")


def test_precio_final_es_polimorfico():
    cd = CD(
        precio_base=Decimal("20.00"),
        peso_kg=Decimal("0.100"),
        costo_envio_por_kg=Decimal("2.00"),
        costo_embalaje=Decimal("0.50"),
    )
    vinilo = Vinilo(
        precio_base=Decimal("20.00"),
        peso_kg=Decimal("0.500"),
        costo_envio_por_kg=Decimal("2.00"),
        costo_embalaje=Decimal("1.50"),
    )

    assert cd.precio_final() == Decimal("20.20000")
    assert vinilo.precio_final() == Decimal("22.50000")


def test_tablas_esperadas_existen_en_postgresql():
    tablas_esperadas = {
        "usuarios",
        "categorias",
        "discos",
        "metodos_pago",
        "verificaciones_tarjeta",
        "pedidos",
        "detalles_pedido",
        "transacciones_pago",
        "facturas",
    }

    with app.app_context():
        tablas_reales = set(inspect(db.engine).get_table_names())

    assert tablas_esperadas <= tablas_reales


def test_fechas_de_creacion_tienen_default_en_postgresql():
    columnas_esperadas = {
        ("usuarios", "fecha_registro"),
        ("categorias", "fecha_creacion"),
        ("categorias", "fecha_actualizacion"),
        ("discos", "fecha_creacion"),
        ("discos", "fecha_actualizacion"),
        ("verificaciones_tarjeta", "fecha_creacion"),
        ("pedidos", "fecha_creacion"),
        ("facturas", "fecha_emision"),
    }

    with app.app_context():
        inspector = inspect(db.engine)
        for tabla, columna in columnas_esperadas:
            definicion = next(
                item
                for item in inspector.get_columns(tabla)
                if item["name"] == columna
            )
            assert definicion["default"] is not None


def test_restricciones_de_calidad_de_usuario_existen():
    restricciones_esperadas = {
        "ck_usuarios_nombre_valido",
        "ck_usuarios_email_normalizado",
        "ck_usuarios_email_formato",
        "ck_usuarios_rol",
    }

    with app.app_context():
        inspector = inspect(db.engine)
        restricciones_reales = {
            restriccion["name"]
            for restriccion in inspector.get_check_constraints("usuarios")
        }

    assert restricciones_esperadas <= restricciones_reales


def test_datos_iniciales_y_polimorfismo_desde_postgresql():
    with app.app_context():
        discos = Disco.query.order_by(Disco.codigo).all()
        categorias = Categoria.query.order_by(Categoria.slug).all()

        assert len(categorias) == 3
        assert len(discos) == 12
        assert any(isinstance(disco, CD) for disco in discos)
        assert any(isinstance(disco, Vinilo) for disco in discos)
        assert all(type(disco) in {CD, Vinilo} for disco in discos)


def test_postgresql_rechaza_stock_negativo():
    with app.app_context():
        categoria = Categoria.query.filter_by(slug="rock").first()
        disco_invalido = CD(
            categoria=categoria,
            codigo="PRUEBA-STOCK-NEGATIVO",
            album="Prueba",
            artista="New Records",
            descripcion="Registro temporal para comprobar la restricción.",
            precio_base=Decimal("10.00"),
            stock=-1,
            peso_kg=Decimal("0.100"),
            costo_envio_por_kg=Decimal("0.00"),
            costo_embalaje=Decimal("0.00"),
        )
        db.session.add(disco_invalido)

        with pytest.raises(IntegrityError):
            db.session.flush()

        db.session.rollback()
