"""Pruebas del módulo de administración, catálogo y aprobación de pedidos — Fase 10."""

import os
import secrets
import pytest

from app import app
from models import CD, Categoria, Disco, Factura, MetodoPago, Pedido, Usuario, Vinilo, db
from payments import crear_verificacion, verificar_pin


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def pass_admin():
    return os.getenv("ADMIN_PASSWORD", "4119c3d7df348fed21f685809151b30e")


def pass_cliente():
    return os.getenv("CLIENTE_DEMO_PASSWORD", "5c45d1a0df71bcead793c6d654a14cbf")


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
        v, pin = crear_verificacion(
            usuario_id,
            {
                "marca": "VISA",
                "ultimos4": "8888",
                "titular": "Cliente Demo",
                "mes_vencimiento": 12,
                "anio_vencimiento": 2028,
            },
        )
        _, tarjeta = verificar_pin(v.token_verificacion, pin)
    return tarjeta


# ── Tests de control de acceso por roles ────────────────────────────────────

def test_rutas_admin_restringidas_a_clientes(client):
    """Los clientes comunes reciben 403 al intentar acceder a rutas administrativas."""
    with client:
        autenticar_cliente(client)
        assert client.get("/admin/dashboard").status_code == 403
        assert client.get("/admin/discos").status_code == 403
        assert client.get("/admin/categorias").status_code == 403
        assert client.get("/admin/pedidos").status_code == 403


def test_admin_dashboard_metricas(client):
    """El administrador accede al dashboard y visualiza las métricas KPI."""
    with client:
        autenticar_admin(client)
        resp = client.get("/admin/dashboard")
        assert resp.status_code == 200
        assert b"Panel de" in resp.data
        assert b"Administraci" in resp.data
        assert b"Discos Activos" in resp.data


# ── Tests de CRUD de Discos ──────────────────────────────────────────────────

def test_crud_disco_crear_y_editar(client):
    with client:
        autenticar_admin(client)

        with app.app_context():
            cat = Categoria.query.filter_by(activo=True).first()
            cat_id = cat.id

        codigo_vinilo = f"NR-VIN-{secrets.token_hex(3).upper()}"

        try:
            # Crear nuevo Vinilo
            resp_crear = client.post(
                "/admin/discos/nuevo",
                data={
                    "formato": "VINILO",
                    "codigo": codigo_vinilo,
                    "album": "Álbum de Prueba Admin",
                    "artista": "Artista Admin",
                    "descripcion": "Descripción del álbum de prueba.",
                    "categoria_id": str(cat_id),
                    "precio_base": "30.00",
                    "stock": "15",
                    "peso_kg": "0.450",
                    "costo_envio_por_kg": "4.00",
                    "costo_embalaje": "3.50",
                    "imagen": "img/placeholder.jpg",
                },
                follow_redirects=True,
            )
            assert resp_crear.status_code == 200
            assert "creado exitosamente" in resp_crear.data.decode("utf-8")

            with app.app_context():
                disco_creado = Disco.query.filter_by(codigo=codigo_vinilo).first()
                assert disco_creado is not None
                assert disco_creado.formato == "VINILO"
                assert isinstance(disco_creado, Vinilo)
                assert disco_creado.costo_embalaje == 3.50
                disco_id = disco_creado.id

            # Editar el disco
            resp_editar = client.post(
                f"/admin/discos/{disco_id}/editar",
                data={
                    "album": "Álbum Modificado Admin",
                    "artista": "Artista Admin",
                    "descripcion": "Descripción modificada.",
                    "categoria_id": str(cat_id),
                    "precio_base": "35.00",
                    "stock": "20",
                    "peso_kg": "0.450",
                    "costo_envio_por_kg": "4.00",
                    "costo_embalaje": "3.50",
                    "imagen": "img/placeholder.jpg",
                },
                follow_redirects=True,
            )
            assert resp_editar.status_code == 200
            assert "actualizado correctamente" in resp_editar.data.decode("utf-8")

            with app.app_context():
                disco_editado = db.session.get(Disco, disco_id)
                assert disco_editado.album == "Álbum Modificado Admin"
                assert disco_editado.precio_base == 35.00
                assert disco_editado.stock == 20
        finally:
            with app.app_context():
                d = Disco.query.filter_by(codigo=codigo_vinilo).first()
                if d:
                    db.session.delete(d)
                    db.session.commit()


def test_crud_disco_desactivar_reactivar(client):
    with client:
        autenticar_admin(client)
        with app.app_context():
            disco = Disco.query.filter_by(activo=True).first()
            disco_id = disco.id

        # Desactivar
        resp_desact = client.post(f"/admin/discos/{disco_id}/desactivar", follow_redirects=True)
        assert resp_desact.status_code == 200

        with app.app_context():
            assert db.session.get(Disco, disco_id).activo is False

        # Reactivar
        resp_react = client.post(f"/admin/discos/{disco_id}/reactivar", follow_redirects=True)
        assert resp_react.status_code == 200

        with app.app_context():
            assert db.session.get(Disco, disco_id).activo is True


# ── Tests de CRUD de Categorías ──────────────────────────────────────────────

def test_crud_categoria_crear_y_desactivar(client):
    with client:
        autenticar_admin(client)
        slug_test = f"genero-{secrets.token_hex(3)}"

        try:
            # Crear categoría
            resp_crear = client.post(
                "/admin/categorias/nueva",
                data={
                    "nombre": "Género Test Admin",
                    "slug": slug_test,
                    "descripcion": "Descripción del género de prueba.",
                    "imagen": "img/placeholder.jpg",
                },
                follow_redirects=True,
            )
            assert resp_crear.status_code == 200
            assert "creada exitosamente" in resp_crear.data.decode("utf-8")

            with app.app_context():
                cat = Categoria.query.filter_by(slug=slug_test).first()
                assert cat is not None
                assert cat.activo is True
                cat_id = cat.id

            # Desactivar
            client.post(f"/admin/categorias/{cat_id}/desactivar", follow_redirects=True)
            with app.app_context():
                assert db.session.get(Categoria, cat_id).activo is False

            # Reactivar
            client.post(f"/admin/categorias/{cat_id}/reactivar", follow_redirects=True)
            with app.app_context():
                assert db.session.get(Categoria, cat_id).activo is True
        finally:
            with app.app_context():
                c = Categoria.query.filter_by(slug=slug_test).first()
                if c:
                    db.session.delete(c)
                    db.session.commit()


# ── Tests de Aprobación y Rechazo de Pedidos ─────────────────────────────────

def test_admin_aprobar_pedido_descuenta_stock(client):
    with client:
        # 1. El cliente crea un pedido con 2 unidades
        autenticar_cliente(client)
        with app.app_context():
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            tarjeta = obtener_o_crear_tarjeta_verificada(usuario.id)
            tarjeta_id = tarjeta.id
            cd = Disco.query.filter_by(codigo="NR-POP-001").first()
            cd_id = cd.id
            stock_inicial = cd.stock

        client.post("/carrito/vaciar")
        client.post(f"/carrito/agregar/{cd_id}", data={"cantidad": 2})
        resp_check = client.post(
            "/checkout/confirmar",
            data={"metodo_pago_id": str(tarjeta_id)},
            follow_redirects=False,
        )
        assert resp_check.status_code == 302

        with app.app_context():
            pedido = Pedido.query.filter_by(cliente_id=usuario.id, estado="PENDIENTE").order_by(Pedido.id.desc()).first()
            numero_pedido = pedido.numero

        # Cerrar sesión del cliente
        client.get("/logout")

        # 2. El administrador aprueba el pedido
        autenticar_admin(client)
        resp_aprobar = client.post(f"/admin/pedidos/{numero_pedido}/aprobar", follow_redirects=True)
        assert resp_aprobar.status_code == 200
        assert "aprobado exitosamente" in resp_aprobar.data.decode("utf-8")

        # 3. Validar estado, cobro, descuento de stock y factura emitida
        with app.app_context():
            p_actualizado = Pedido.query.filter_by(numero=numero_pedido).first()
            assert p_actualizado.estado == "APROBADO"
            assert p_actualizado.transaccion_pago.estado == "APROBADA"
            assert p_actualizado.fecha_revision is not None
            assert p_actualizado.administrador_revisor_id is not None

            # Stock descontado exactamente en 2 unidades
            cd_actualizado = db.session.get(Disco, cd_id)
            assert cd_actualizado.stock == stock_inicial - 2

            # Factura oficial generada
            factura = Factura.query.filter_by(pedido_id=p_actualizado.id, tipo="FACTURA_FINAL").first()
            assert factura is not None

            # Restaurar stock para pruebas restantes
            cd_actualizado.stock = stock_inicial
            db.session.commit()


def test_admin_rechazar_pedido_con_motivo(client):
    with client:
        # 1. El cliente crea un pedido
        autenticar_cliente(client)
        with app.app_context():
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            tarjeta = obtener_o_crear_tarjeta_verificada(usuario.id)
            tarjeta_id = tarjeta.id
            cd = Disco.query.filter_by(codigo="NR-POP-001").first()
            cd_id = cd.id
            stock_inicial = cd.stock

        client.post("/carrito/vaciar")
        client.post(f"/carrito/agregar/{cd_id}", data={"cantidad": 1})
        client.post(
            "/checkout/confirmar",
            data={"metodo_pago_id": str(tarjeta_id)},
            follow_redirects=False,
        )

        with app.app_context():
            pedido = Pedido.query.filter_by(cliente_id=usuario.id, estado="PENDIENTE").order_by(Pedido.id.desc()).first()
            numero_pedido = pedido.numero

        # Cerrar sesión del cliente
        client.get("/logout")

        # 2. El administrador rechaza el pedido
        autenticar_admin(client)
        resp_rechazar = client.post(
            f"/admin/pedidos/{numero_pedido}/rechazar",
            data={"motivo": "Stock físico dañado en depósito."},
            follow_redirects=True,
        )
        assert resp_rechazar.status_code == 200
        assert "rechazado correctamente" in resp_rechazar.data.decode("utf-8")

        # 3. Validar estado y que el stock NO fue alterado
        with app.app_context():
            p_actualizado = Pedido.query.filter_by(numero=numero_pedido).first()
            assert p_actualizado.estado == "RECHAZADO"
            assert p_actualizado.motivo_rechazo == "Stock físico dañado en depósito."
            assert p_actualizado.transaccion_pago.estado == "RECHAZADA"

            cd_actualizado = db.session.get(Disco, cd_id)
            assert cd_actualizado.stock == stock_inicial


def test_admin_aprobar_falla_sin_stock(client):
    """Si no hay stock suficiente, la aprobación falla y no altera el pedido ni el stock."""
    with client:
        autenticar_cliente(client)
        with app.app_context():
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            tarjeta = obtener_o_crear_tarjeta_verificada(usuario.id)
            tarjeta_id = tarjeta.id
            cd = Disco.query.filter_by(codigo="NR-POP-001").first()
            cd_id = cd.id

        client.post("/carrito/vaciar")
        client.post(f"/carrito/agregar/{cd_id}", data={"cantidad": 1})
        client.post(
            "/checkout/confirmar",
            data={"metodo_pago_id": str(tarjeta_id)},
            follow_redirects=False,
        )

        with app.app_context():
            pedido = Pedido.query.filter_by(cliente_id=usuario.id, estado="PENDIENTE").order_by(Pedido.id.desc()).first()
            numero_pedido = pedido.numero
            # Forzar stock a 0 antes de la aprobación
            cd_obj = db.session.get(Disco, cd_id)
            cd_obj.stock = 0
            db.session.commit()

        # Cerrar sesión del cliente
        client.get("/logout")

        # El admin intenta aprobar
        autenticar_admin(client)
        resp = client.post(f"/admin/pedidos/{numero_pedido}/aprobar", follow_redirects=True)
        assert resp.status_code == 200
        assert "No hay stock suficiente" in resp.data.decode("utf-8")

        with app.app_context():
            p_verificado = Pedido.query.filter_by(numero=numero_pedido).first()
            assert p_verificado.estado == "PENDIENTE"
            # Restaurar stock para pruebas futuras
            cd_obj = db.session.get(Disco, cd_id)
            cd_obj.stock = 18
            db.session.commit()
