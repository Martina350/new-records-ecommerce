"""Pruebas del módulo de reportes analíticos de ventas — Fase 11."""

import os
import secrets
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app import app
from models import (
    CD,
    Categoria,
    DetallePedido,
    Disco,
    MetodoPago,
    Pedido,
    TransaccionPago,
    Usuario,
    Vinilo,
    ahora_utc,
    db,
)
from services import (
    obtener_ranking_categorias,
    obtener_ranking_discos,
    obtener_reporte_ventas_temporal,
    obtener_resumen_metricas_ventas,
)


@pytest.fixture(autouse=True)
def limpiar_pedidos_analiticos(client):
    """Garantiza aislamiento de métricas eliminando pedidos previos en la transacción."""
    with app.app_context():
        DetallePedido.query.delete()
        TransaccionPago.query.delete()
        Pedido.query.delete()
        db.session.commit()
    yield


def pass_admin():
    return os.environ["ADMIN_PASSWORD"]


def pass_cliente():
    return os.environ["CLIENTE_DEMO_PASSWORD"]


def autenticar_admin(client):
    return client.post(
        "/login",
        data={"email": "admin@newrecords.local", "password": pass_admin()},
        follow_redirects=True,
    )


def autenticar_cliente(client):
    return client.post(
        "/login",
        data={"email": "cliente@newrecords.local", "password": pass_cliente()},
        follow_redirects=True,
    )


def obtener_o_crear_tarjeta_verificada(usuario_id):
    tarjeta = MetodoPago.query.filter_by(usuario_id=usuario_id, activo=True).first()
    if not tarjeta:
        tarjeta = MetodoPago(
            usuario_id=usuario_id,
            token=f"TOK-TEST-{secrets.token_hex(8)}",
            marca="VISA",
            ultimos4="8888",
            titular="Cliente Demo",
            mes_vencimiento=12,
            anio_vencimiento=2028,
            fecha_verificacion=ahora_utc(),
            activo=True,
            predeterminado=True,
        )
        db.session.add(tarjeta)
        db.session.flush()
    return tarjeta


def crear_pedido_auxiliar(cliente_id, metodo_id=None, estado="APROBADO", fecha=None):
    """Crea un pedido con su transacción asociada para pruebas analíticas."""
    if metodo_id is None:
        tarjeta = obtener_o_crear_tarjeta_verificada(cliente_id)
        metodo_id = tarjeta.id

    numero = f"NR-TEST-{secrets.token_hex(4).upper()}"
    fecha_pedido = fecha or ahora_utc()

    pedido = Pedido(
        numero=numero,
        cliente_id=cliente_id,
        metodo_pago_id=metodo_id,
        estado=estado,
        total=Decimal("0"),
        fecha_creacion=fecha_pedido,
        motivo_rechazo="Motivo de rechazo de prueba" if estado == "RECHAZADO" else None,
    )
    db.session.add(pedido)
    db.session.flush()

    estado_txn = (
        "APROBADA"
        if estado == "APROBADO"
        else ("RECHAZADA" if estado == "RECHAZADO" else "PENDIENTE")
    )

    transaccion = TransaccionPago(
        pedido_id=pedido.id,
        metodo_pago_id=metodo_id,
        monto=Decimal("0"),
        estado=estado_txn,
        referencia=f"TXN-TEST-{secrets.token_hex(8).upper()}",
        fecha_procesamiento=fecha_pedido,
    )
    db.session.add(transaccion)
    return pedido


def agregar_detalle_auxiliar(pedido, disco, cantidad, precio_unitario):
    """Añade una línea de detalle a un pedido y actualiza su total."""
    subtotal = Decimal(str(precio_unitario)) * cantidad
    detalle = DetallePedido(
        pedido_id=pedido.id,
        disco_id=disco.id,
        album=disco.album,
        artista=disco.artista,
        formato=disco.formato,
        precio_unitario=Decimal(str(precio_unitario)),
        cantidad=cantidad,
    )
    db.session.add(detalle)
    pedido.total += subtotal
    if pedido.transaccion_pago:
        pedido.transaccion_pago.monto += subtotal


# ── Tests de Acceso y Autorización ──────────────────────────────────────────


def test_reportes_requiere_autenticacion_y_rol_admin(client):
    """Usuarios anónimos o clientes no pueden ingresar a los reportes administrativos."""
    # Anónimo
    resp_anon = client.get("/admin/reportes")
    assert resp_anon.status_code in (302, 403)

    # Cliente
    with client:
        autenticar_cliente(client)
        resp_cliente = client.get("/admin/reportes")
        assert resp_cliente.status_code == 403
        client.post("/logout", follow_redirects=True)

    # Administrador
    with client:
        autenticar_admin(client)
        resp_admin = client.get("/admin/reportes")
        assert resp_admin.status_code == 200
        assert b"Reportes y Anal" in resp_admin.data
        assert b"Ventas" in resp_admin.data


# ── Tests de Exclusión de Estados No Aprobados ───────────────────────────────

def test_reportes_excluyen_pedidos_pendientes_y_rechazados(client):
    """Los pedidos PENDIENTE y RECHAZADO no deben alterar los ingresos ni los rankings."""
    with app.app_context():
        cliente = Usuario.query.filter_by(rol="cliente").first()
        disco = Disco.query.filter_by(activo=True).first()

        # Crear pedido pendiente
        ped_pendiente = crear_pedido_auxiliar(cliente.id, estado="PENDIENTE")
        agregar_detalle_auxiliar(ped_pendiente, disco, 3, Decimal("50.00"))

        # Crear pedido rechazado
        ped_rechazado = crear_pedido_auxiliar(cliente.id, estado="RECHAZADO")
        ped_rechazado.motivo_rechazo = "Fondos insuficientes"
        agregar_detalle_auxiliar(ped_rechazado, disco, 2, Decimal("40.00"))

        db.session.commit()

        # Verificar que las métricas globales permanezcan en 0 (o solo con aprobados previos)
        resumen = obtener_resumen_metricas_ventas()
        ranking_d = obtener_ranking_discos()
        ranking_c = obtener_ranking_categorias()
        reporte_temp = obtener_reporte_ventas_temporal("diario")

        # Ninguno de los 5 discos de estos pedidos no aprobados debe sumarse
        unidades_reportadas = sum(d["total_unidades"] for d in ranking_d)
        assert unidades_reportadas == 0
        assert resumen["total_pedidos"] == 0
        assert resumen["total_unidades"] == 0
        assert resumen["total_facturado"] == 0.0
        assert len(reporte_temp) == 0


# ── Tests de Cálculo y Agregaciones de Ventas Aprobadas ───────────────────────

def test_reporte_ventas_calculos_y_ticket_promedio(client):
    """Verifica el cálculo exacto de ingresos, unidades y ticket promedio tras aprobación."""
    with app.app_context():
        cliente = Usuario.query.filter_by(rol="cliente").first()
        discos = Disco.query.filter_by(activo=True).all()

        disco_1 = discos[0]
        disco_2 = discos[1]

        # Pedido 1: 2 unidades de disco 1 a $25 = $50
        ped_1 = crear_pedido_auxiliar(cliente.id, estado="APROBADO")
        agregar_detalle_auxiliar(ped_1, disco_1, 2, Decimal("25.00"))

        # Pedido 2: 1 unidad de disco 1 a $25 + 3 unidades de disco 2 a $30 = $25 + $90 = $115
        ped_2 = crear_pedido_auxiliar(cliente.id, estado="APROBADO")
        agregar_detalle_auxiliar(ped_2, disco_1, 1, Decimal("25.00"))
        agregar_detalle_auxiliar(ped_2, disco_2, 3, Decimal("30.00"))

        db.session.commit()

        resumen = obtener_resumen_metricas_ventas()
        # Total facturado: $50 + $115 = $165.00
        # Total unidades: 2 + 1 + 3 = 6
        # Total pedidos: 2
        # Ticket promedio: 165 / 2 = 82.50
        assert resumen["total_pedidos"] == 2
        assert resumen["total_unidades"] == 6
        assert resumen["total_facturado"] == 165.0
        assert resumen["ticket_promedio"] == 82.50


def test_reporte_ventas_agrupaciones_temporales(client):
    """Verifica las agrupaciones diaria, semanal, mensual y anual."""
    with app.app_context():
        cliente = Usuario.query.filter_by(rol="cliente").first()
        disco = Disco.query.filter_by(activo=True).first()

        ped = crear_pedido_auxiliar(cliente.id, estado="APROBADO")
        agregar_detalle_auxiliar(ped, disco, 4, Decimal("20.00"))
        db.session.commit()

        # Diario
        diario = obtener_reporte_ventas_temporal("diario")
        assert len(diario) >= 1
        assert diario[0]["total_pedidos"] == 1
        assert diario[0]["total_unidades"] == 4
        assert diario[0]["total_facturado"] == 80.0

        # Semanal
        semanal = obtener_reporte_ventas_temporal("semanal")
        assert len(semanal) >= 1
        assert "Semana" in semanal[0]["etiqueta"]
        assert semanal[0]["total_unidades"] == 4

        # Mensual
        mensual = obtener_reporte_ventas_temporal("mensual")
        assert len(mensual) >= 1
        assert mensual[0]["total_unidades"] == 4
        assert mensual[0]["total_facturado"] == 80.0

        # Anual
        anual = obtener_reporte_ventas_temporal("anual")
        assert len(anual) >= 1
        assert anual[0]["etiqueta"] == str(ped.fecha_creacion.year)
        assert anual[0]["total_unidades"] == 4
        assert anual[0]["total_facturado"] == 80.0


def test_reporte_anual_consolida_meses_del_mismo_anio(client):
    """Mensual separa meses y anual los consolida en una sola fila."""
    with app.app_context():
        cliente = Usuario.query.filter_by(rol="cliente").first()
        disco = Disco.query.filter_by(activo=True).first()

        enero = crear_pedido_auxiliar(
            cliente.id,
            estado="APROBADO",
            fecha=datetime(2025, 1, 15, tzinfo=timezone.utc),
        )
        agregar_detalle_auxiliar(enero, disco, 1, Decimal("10.00"))
        febrero = crear_pedido_auxiliar(
            cliente.id,
            estado="APROBADO",
            fecha=datetime(2025, 2, 15, tzinfo=timezone.utc),
        )
        agregar_detalle_auxiliar(febrero, disco, 2, Decimal("10.00"))
        db.session.commit()

        mensual = obtener_reporte_ventas_temporal("mensual")
        anual = obtener_reporte_ventas_temporal("anual")

        assert len(mensual) == 2
        assert len(anual) == 1
        assert anual[0]["etiqueta"] == "2025"
        assert anual[0]["total_pedidos"] == 2
        assert anual[0]["total_unidades"] == 3
        assert anual[0]["total_facturado"] == 30.0


# ── Tests de Rankings (Discos y Géneros) ──────────────────────────────────────

def test_ranking_discos_orden_y_porcentajes(client):
    """El ranking de discos debe ordenar de mayor a menor demanda y calcular porcentaje."""
    with app.app_context():
        cliente = Usuario.query.filter_by(rol="cliente").first()
        discos = Disco.query.filter_by(activo=True).all()

        disco_mas_vendido = discos[0]
        disco_menos_vendido = discos[1]

        ped = crear_pedido_auxiliar(cliente.id, estado="APROBADO")
        agregar_detalle_auxiliar(ped, disco_mas_vendido, 10, Decimal("15.00"))
        agregar_detalle_auxiliar(ped, disco_menos_vendido, 2, Decimal("30.00"))
        db.session.commit()

        ranking = obtener_ranking_discos(limite=5)
        assert len(ranking) >= 2
        assert ranking[0]["disco_id"] == disco_mas_vendido.id
        assert ranking[0]["total_unidades"] == 10
        assert ranking[0]["porcentaje_relativo"] == 100.0
        assert ranking[0]["posicion"] == 1

        assert ranking[1]["disco_id"] == disco_menos_vendido.id
        assert ranking[1]["total_unidades"] == 2
        assert ranking[1]["porcentaje_relativo"] == 20.0
        assert ranking[1]["posicion"] == 2


def test_ranking_categorias_participacion(client):
    """El ranking de categorías debe agrupar los discos por género musical."""
    with app.app_context():
        cliente = Usuario.query.filter_by(rol="cliente").first()
        
        categorias = Categoria.query.filter_by(activo=True).all()
        cat_rock = next((c for c in categorias if c.slug == "rock"), categorias[0])
        cat_pop = next((c for c in categorias if c.slug == "pop"), categorias[1])

        disco_rock = Disco.query.filter_by(categoria_id=cat_rock.id, activo=True).first()
        disco_pop = Disco.query.filter_by(categoria_id=cat_pop.id, activo=True).first()

        ped = crear_pedido_auxiliar(cliente.id, estado="APROBADO")
        # $80 en Rock
        agregar_detalle_auxiliar(ped, disco_rock, 4, Decimal("20.00"))
        # $20 en Pop
        agregar_detalle_auxiliar(ped, disco_pop, 1, Decimal("20.00"))
        db.session.commit()

        ranking_cat = obtener_ranking_categorias()
        assert len(ranking_cat) >= 2
        
        # El primero debe ser Rock ($80 de $100 = 80%)
        top_cat = ranking_cat[0]
        assert top_cat["categoria_id"] == cat_rock.id
        assert top_cat["total_facturado"] == 80.0
        assert top_cat["porcentaje_participacion"] == 80.0

        # El segundo debe ser Pop ($20 de $100 = 20%)
        segunda_cat = ranking_cat[1]
        assert segunda_cat["categoria_id"] == cat_pop.id
        assert segunda_cat["total_facturado"] == 20.0
        assert segunda_cat["porcentaje_participacion"] == 20.0


# ── Test de Renderizado y Parámetros HTTP ─────────────────────────────────────

def test_vistas_reportes_filtros_http(client):
    """El administrador puede filtrar las vistas de reportes por query params."""
    with client:
        autenticar_admin(client)

        for p in ("diario", "semanal", "mensual", "anual"):
            resp = client.get(f"/admin/reportes?periodo={p}")
            assert resp.status_code == 200
            assert b"Evoluci" in resp.data
            assert b"Top Discos" in resp.data
            assert b"por G" in resp.data
