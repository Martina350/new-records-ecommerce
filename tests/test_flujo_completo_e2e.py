"""Pruebas de integración de flujo completo (End-to-End) — Fase 13.

Verifica el ciclo de vida completo de New Records:
- Registro de cliente, navegación, carrito polimórfico, pago con PIN y checkout.
- Aprobación administrativa, descuento concurrente de stock, facturas PDF y reportes analíticos.
- Rechazo de pedidos con motivo y preservación de existencias.
- Gestión CRUD y desactivación lógica de catálogo.
"""

import os
import secrets
from decimal import Decimal

from app import app
from models import CD, Categoria, Disco, Factura, MetodoPago, Pedido, Usuario, VerificacionTarjeta, Vinilo, db
from payments import crear_verificacion


def pass_admin():
    return os.environ["ADMIN_PASSWORD"]


def pass_cliente():
    return os.environ["CLIENTE_DEMO_PASSWORD"]


def autenticar_usuario(client, email, password):
    """Auxiliar para iniciar sesión y seguir redirecciones."""
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_flujo_completo_e2e_compra_aprobacion_factura_y_reportes(client):
    """Flujo completo de compra: Registro -> Carrito -> PIN -> Checkout -> Aprobación Admin -> Factura PDF -> Reportes."""
    email_cliente = f"cliente_e2e_{secrets.token_hex(4)}@example.com"
    password_cliente = "PasswordE2E123!"
    nombre_cliente = "Cliente E2E Automatizado"

    with client:
        # ── 1. Registro de nuevo cliente ──────────────────────────────────────────
        resp_reg = client.post(
            "/registro",
            data={
                "nombre": nombre_cliente,
                "email": email_cliente,
                "password": password_cliente,
                "confirmar_password": password_cliente,
            },
            follow_redirects=True,
        )
        assert resp_reg.status_code == 200
        assert b"creada exitosamente" in resp_reg.data

        # ── 2. Login del cliente ──────────────────────────────────────────────────
        resp_login = autenticar_usuario(client, email_cliente, password_cliente)
        assert resp_login.status_code == 200

        # ── 3. Navegación del catálogo y agregado de productos polimórficos ───────
        with app.app_context():
            cd_demo = Disco.query.filter_by(formato="CD", activo=True).first()
            vinilo_demo = Disco.query.filter_by(formato="VINILO", activo=True).first()
            assert cd_demo is not None
            assert vinilo_demo is not None
            stock_inicial_cd = cd_demo.stock
            stock_inicial_vinilo = vinilo_demo.stock
            cd_id = cd_demo.id
            vinilo_id = vinilo_demo.id
            cliente_obj = Usuario.query.filter_by(email=email_cliente).first()
            assert cliente_obj is not None
            cliente_id = cliente_obj.id

        # Agregar CD y Vinilo al carrito
        client.post(f"/carrito/agregar/{cd_id}", data={"cantidad": 1}, follow_redirects=True)
        client.post(f"/carrito/agregar/{vinilo_id}", data={"cantidad": 1}, follow_redirects=True)

        resp_carrito = client.get("/carrito")
        assert resp_carrito.status_code == 200

        # ── 4. Registro y verificación de tarjeta con PIN ─────────────────────────
        with app.app_context():
            verificacion, pin_plano = crear_verificacion(
                cliente_id,
                {
                    "marca": "VISA",
                    "ultimos4": "9999",
                    "titular": nombre_cliente,
                    "mes_vencimiento": 12,
                    "anio_vencimiento": 2030,
                },
            )
            token_verif = verificacion.token_verificacion

        resp_pin = client.post(
            f"/pago/verificar/{token_verif}",
            data={"pin": pin_plano},
            follow_redirects=True,
        )
        assert resp_pin.status_code == 200

        with app.app_context():
            metodo = MetodoPago.query.filter_by(usuario_id=cliente_id, activo=True).first()
            assert metodo is not None
            metodo_id = metodo.id

        # ── 5. Checkout y generación de Comprobante Pendiente ──────────────────────
        resp_checkout = client.post(
            "/checkout/confirmar",
            data={"metodo_pago_id": str(metodo_id)},
            follow_redirects=True,
        )
        assert resp_checkout.status_code == 200

        with app.app_context():
            pedido_creado = Pedido.query.filter_by(cliente_id=cliente_id).order_by(Pedido.id.desc()).first()
            assert pedido_creado is not None
            assert pedido_creado.estado == "PENDIENTE"
            numero_pedido = pedido_creado.numero

            # Comprobar que existe el comprobante inicial
            comprobante = Factura.query.filter_by(pedido_id=pedido_creado.id, tipo="COMPROBANTE_PENDIENTE").first()
            assert comprobante is not None

        # Descargar comprobante en PDF como cliente
        resp_pdf_comp = client.get(f"/pedidos/{numero_pedido}/comprobante")
        assert resp_pdf_comp.status_code == 200
        assert resp_pdf_comp.content_type == "application/pdf"

        # Intentar descargar Factura Final antes de aprobar debe fallar
        resp_pdf_fac_bloqueada = client.get(f"/pedidos/{numero_pedido}/factura")
        assert resp_pdf_fac_bloqueada.status_code in (302, 400, 403, 404)

        # Cliente cierra sesión
        client.post("/logout", follow_redirects=True)

        # ── 6. Administrador aprueba el pedido ─────────────────────────────────────
        autenticar_usuario(client, "admin@newrecords.local", pass_admin())

        # Ver pedido en detalle de administrador
        resp_admin_det = client.get(f"/admin/pedidos/{numero_pedido}")
        assert resp_admin_det.status_code == 200

        # Aprobar pedido
        resp_aprobar = client.post(f"/admin/pedidos/{numero_pedido}/aprobar", follow_redirects=True)
        assert resp_aprobar.status_code == 200

        with app.app_context():
            db.session.expire_all()
            ped_aprobado = Pedido.query.filter_by(numero=numero_pedido).first()
            assert ped_aprobado.estado == "APROBADO"

            # Verificar descuento concurrente de stock
            cd_actual = db.session.get(Disco, cd_id)
            vinilo_actual = db.session.get(Disco, vinilo_id)
            assert cd_actual.stock == stock_inicial_cd - 1
            assert vinilo_actual.stock == stock_inicial_vinilo - 1

            # Verificar factura final emitida
            factura_final = Factura.query.filter_by(pedido_id=ped_aprobado.id, tipo="FACTURA_FINAL").first()
            assert factura_final is not None

        # ── 7. Administrador consulta reportes analíticos de ventas ────────────────
        resp_reportes = client.get("/admin/reportes?periodo=diario")
        assert resp_reportes.status_code == 200
        assert b"Reportes y Anal" in resp_reportes.data

        # Administrador cierra sesión
        client.post("/logout", follow_redirects=True)

        # ── 8. Cliente descarga su Factura Final emitida en PDF ────────────────────
        autenticar_usuario(client, email_cliente, password_cliente)
        resp_pdf_fac = client.get(f"/pedidos/{numero_pedido}/factura")
        assert resp_pdf_fac.status_code == 200
        assert resp_pdf_fac.content_type == "application/pdf"
        assert resp_pdf_fac.data.startswith(b"%PDF")


def test_flujo_rechazo_pedido_con_motivo_no_altera_stock(client):
    """Flujo de rechazo de pedido: exige motivo y no reduce el stock."""
    email_cliente = f"cliente_rech_{secrets.token_hex(4)}@example.com"
    password = "Password123!"

    with client:
        # 1. Crear cliente y pedido
        client.post(
            "/registro",
            data={"nombre": "Cliente Rechazo", "email": email_cliente, "password": password, "confirmar_password": password},
            follow_redirects=True,
        )
        autenticar_usuario(client, email_cliente, password)

        with app.app_context():
            disco = Disco.query.filter_by(activo=True).first()
            disco_id = disco.id
            stock_antes = disco.stock
            cliente = Usuario.query.filter_by(email=email_cliente).first()
            assert cliente is not None
            cliente_id = cliente.id

            verificacion, pin_plano = crear_verificacion(
                cliente_id,
                {
                    "marca": "MASTERCARD",
                    "ultimos4": "7777",
                    "titular": "Cliente Rechazo",
                    "mes_vencimiento": 11,
                    "anio_vencimiento": 2029,
                },
            )
            token_verif = verificacion.token_verificacion

        client.post(f"/pago/verificar/{token_verif}", data={"pin": pin_plano}, follow_redirects=True)

        with app.app_context():
            metodo = MetodoPago.query.filter_by(usuario_id=cliente_id, activo=True).first()
            metodo_id = metodo.id

        client.post(f"/carrito/agregar/{disco_id}", data={"cantidad": 2}, follow_redirects=True)
        client.post("/checkout/confirmar", data={"metodo_pago_id": str(metodo_id)}, follow_redirects=True)

        with app.app_context():
            pedido = Pedido.query.filter_by(cliente_id=cliente_id).order_by(Pedido.id.desc()).first()
            numero_ped = pedido.numero

        client.post("/logout", follow_redirects=True)

        # 2. Administrador rechaza con motivo
        autenticar_usuario(client, "admin@newrecords.local", pass_admin())
        motivo = "Dirección de entrega fuera de la zona de cobertura"
        resp_rechazo = client.post(f"/admin/pedidos/{numero_ped}/rechazar", data={"motivo": motivo}, follow_redirects=True)
        assert resp_rechazo.status_code == 200

        with app.app_context():
            db.session.expire_all()
            ped_rech = Pedido.query.filter_by(numero=numero_ped).first()
            assert ped_rech.estado == "RECHAZADO"
            assert ped_rech.motivo_rechazo == motivo

            # El stock debe permanecer intacto
            disco_despues = db.session.get(Disco, disco_id)
            assert disco_despues.stock == stock_antes


def test_flujo_administracion_catalogo_crud_y_desactivacion(client):
    """Flujo de administración: Crear categoría -> Crear disco -> Desactivación suave -> Reactivación."""
    with client:
        autenticar_usuario(client, "admin@newrecords.local", pass_admin())

        # 1. Crear categoría
        slug_cat = f"jazz-{secrets.token_hex(3)}"
        resp_cat = client.post(
            "/admin/categorias/nueva",
            data={"nombre": "Jazz & Blues", "slug": slug_cat, "descripcion": "Grandes clásicos del jazz y blues."},
            follow_redirects=True,
        )
        assert resp_cat.status_code == 200

        with app.app_context():
            cat_creada = Categoria.query.filter_by(slug=slug_cat).first()
            assert cat_creada is not None
            cat_id = cat_creada.id

        # 2. Crear disco CD en esa categoría
        codigo_disco = f"NR-JAZZ-{secrets.token_hex(3).upper()}"
        resp_disco = client.post(
            "/admin/discos/nuevo",
            data={
                "categoria_id": cat_id,
                "formato": "CD",
                "codigo": codigo_disco,
                "album": "Kind of Blue",
                "artista": "Miles Davis",
                "descripcion": "Obra cumbre del jazz modal.",
                "precio_base": "25.50",
                "stock": 10,
                "peso_kg": "0.150",
                "costo_envio_por_kg": "2.50",
                "costo_embalaje": "0.50",
                "imagen": "img/productos/fn.jpg",
            },
            follow_redirects=True,
        )
        assert resp_disco.status_code == 200

        with app.app_context():
            disco_creado = Disco.query.filter_by(codigo=codigo_disco).first()
            assert disco_creado is not None
            disco_id = disco_creado.id
            assert disco_creado.activo is True

        # 3. Desactivación lógica del disco
        client.post(f"/admin/discos/{disco_id}/desactivar", follow_redirects=True)
        with app.app_context():
            db.session.expire_all()
            disco_desc = db.session.get(Disco, disco_id)
            assert disco_desc.activo is False

        # 4. Reactivación lógica del disco
        client.post(f"/admin/discos/{disco_id}/reactivar", follow_redirects=True)
        with app.app_context():
            db.session.expire_all()
            disco_react = db.session.get(Disco, disco_id)
            assert disco_react.activo is True
