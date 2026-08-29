"""Pruebas del sistema de pedidos, stock y cobro simulado — Fase 8."""

import os
import secrets
import pytest
from flask import session

from app import app
from models import Disco, MetodoPago, Pedido, Usuario, db
from payments import crear_verificacion, verificar_pin
from services import procesar_checkout


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def pass_cliente():
    return os.getenv("CLIENTE_DEMO_PASSWORD", "5c45d1a0df71bcead793c6d654a14cbf")


def autenticar_cliente(client):
    return client.post(
        "/login",
        data={"email": "cliente@newrecords.local", "password": pass_cliente()},
        follow_redirects=True,
    )


def obtener_o_crear_tarjeta_verificada(usuario_id):
    """Crea una tarjeta verificada para pruebas si no existe una activa."""
    tarjeta = MetodoPago.query.filter_by(usuario_id=usuario_id, activo=True).first()
    if not tarjeta:
        v, pin = crear_verificacion(
            usuario_id,
            {
                "marca": "VISA",
                "ultimos4": "4242",
                "titular": "Cliente Demo",
                "mes_vencimiento": 12,
                "anio_vencimiento": 2028,
            },
        )
        _, tarjeta = verificar_pin(v.token_verificacion, pin)
    return tarjeta


# ── Tests de control de acceso ──────────────────────────────────────────────

def test_pedidos_requiere_login(client):
    resp = client.get("/pedidos", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    resp_post = client.post("/checkout/confirmar", follow_redirects=False)
    assert resp_post.status_code == 302
    assert "/login" in resp_post.headers["Location"]


# ── Tests de creación y flujo de pedidos ────────────────────────────────────

def test_crear_pedido_exitoso(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            tarjeta = obtener_o_crear_tarjeta_verificada(usuario.id)
            tarjeta_id = tarjeta.id
            cd = Disco.query.filter_by(codigo="NR-POP-001").first()
            cd_id = cd.id

        # Vaciar carrito y agregar producto
        client.post("/carrito/vaciar")
        client.post(f"/carrito/agregar/{cd_id}", data={"cantidad": 2})

        assert session["carrito"].get(str(cd_id)) == 2

        # Confirmar checkout
        resp = client.post(
            "/checkout/confirmar",
            data={"metodo_pago_id": str(tarjeta_id)},
            follow_redirects=False,
        )

        assert resp.status_code == 302
        assert "/pedidos/NR-" in resp.headers["Location"]

        # Verificar que el carrito se vació
        assert session.get("carrito") == {} or str(cd_id) not in session.get("carrito", {})

        # Verificar persistencia en base de datos
        with app.app_context():
            pedido = Pedido.query.filter_by(cliente_id=usuario.id).order_by(Pedido.id.desc()).first()
            assert pedido is not None
            assert pedido.estado == "PENDIENTE"
            assert pedido.total > 0
            assert len(pedido.detalles) == 1
            assert pedido.transaccion_pago is not None
            assert pedido.transaccion_pago.estado == "PENDIENTE"


def test_formato_inmutable_detalles(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            tarjeta = obtener_o_crear_tarjeta_verificada(usuario.id)
            tarjeta_id = tarjeta.id
            vinilo = Disco.query.filter_by(codigo="NR-ROC-001").first()  # Dark Side of the Moon
            vinilo_id = vinilo.id
            precio_esperado = vinilo.precio_final()

        client.post("/carrito/vaciar")
        client.post(f"/carrito/agregar/{vinilo_id}", data={"cantidad": 1})

        client.post(
            "/checkout/confirmar",
            data={"metodo_pago_id": str(tarjeta_id)},
            follow_redirects=True,
        )

        with app.app_context():
            pedido = Pedido.query.filter_by(cliente_id=usuario.id).order_by(Pedido.id.desc()).first()
            detalle = pedido.detalles[0]
            assert detalle.album == "The Dark Side of the Moon"
            assert detalle.artista == "Pink Floyd"
            assert detalle.formato == "VINILO"
            assert detalle.precio_unitario == precio_esperado
            assert detalle.cantidad == 1
            assert detalle.subtotal == precio_esperado


def test_checkout_falla_sin_metodo_pago(client):
    with client:
        autenticar_cliente(client)
        with app.app_context():
            cd = Disco.query.filter_by(codigo="NR-POP-001").first()
            cd_id = cd.id

        client.post("/carrito/vaciar")
        client.post(f"/carrito/agregar/{cd_id}", data={"cantidad": 1})

        resp = client.post("/checkout/confirmar", data={}, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Debes seleccionar un m\xc3\xa9todo de pago" in resp.data


def test_checkout_falla_con_tarjeta_ajena(client):
    with client:
        autenticar_cliente(client)
        with app.app_context():
            admin = Usuario.query.filter_by(rol="administrador").first()
            tarjeta_admin = obtener_o_crear_tarjeta_verificada(admin.id)
            tarjeta_admin_id = tarjeta_admin.id
            cd = Disco.query.filter_by(codigo="NR-POP-001").first()
            cd_id = cd.id

        client.post("/carrito/vaciar")
        client.post(f"/carrito/agregar/{cd_id}", data={"cantidad": 1})

        resp = client.post(
            "/checkout/confirmar",
            data={"metodo_pago_id": str(tarjeta_admin_id)},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert "no es válido" in resp.data.decode("utf-8") or "no está disponible" in resp.data.decode("utf-8")


def test_ver_historial_pedidos_cliente(client):
    with client:
        autenticar_cliente(client)
        resp = client.get("/pedidos")
        assert resp.status_code == 200
        assert b"Mis" in resp.data
        assert b"Pedidos" in resp.data


def test_ver_detalle_pedido_propio(client):
    with client:
        autenticar_cliente(client)
        with app.app_context():
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            pedido = Pedido.query.filter_by(cliente_id=usuario.id).first()
            numero_pedido = pedido.numero

        resp = client.get(f"/pedidos/{numero_pedido}")
        assert resp.status_code == 200
        assert numero_pedido.encode("utf-8") in resp.data
        assert b"PENDIENTE" in resp.data


def test_cliente_no_puede_ver_pedido_ajeno(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            admin = Usuario.query.filter_by(rol="administrador").first()
            tarjeta_admin = obtener_o_crear_tarjeta_verificada(admin.id)
            numero_pedido_admin = f"NR-ADM-{secrets.token_hex(4).upper()}"
            
            # Crear un pedido para el administrador
            pedido_admin = Pedido(
                numero=numero_pedido_admin,
                cliente_id=admin.id,
                metodo_pago_id=tarjeta_admin.id,
                total=50.00,
                estado="PENDIENTE",
            )
            db.session.add(pedido_admin)
            db.session.commit()

        # El cliente intenta consultar el pedido del admin
        resp = client.get(f"/pedidos/{numero_pedido_admin}")
        assert resp.status_code == 404
