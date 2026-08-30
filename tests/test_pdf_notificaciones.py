"""Pruebas de generación de comprobantes y facturas PDF y notificaciones — Fase 9."""

import os
import secrets
from app import app
from mailer import notificar_cambio_estado, notificar_creacion_pedido
from models import Disco, Factura, MetodoPago, Pedido, Usuario, db
from payments import crear_verificacion, verificar_pin
from pdf_generator import generar_pdf_pedido

def pass_cliente():
    return os.getenv("CLIENTE_DEMO_PASSWORD", "5c45d1a0df71bcead793c6d654a14cbf")


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
                "ultimos4": "7777",
                "titular": "Cliente Demo",
                "mes_vencimiento": 12,
                "anio_vencimiento": 2029,
            },
        )
        _, tarjeta = verificar_pin(v.token_verificacion, pin)
    return tarjeta


def crear_pedido_cliente(client):
    """Crea un pedido completo para que cada prueba de PDF sea independiente."""
    with app.app_context():
        usuario_id = Usuario.query.filter_by(
            email="cliente@newrecords.local"
        ).first().id
        tarjeta_id = obtener_o_crear_tarjeta_verificada(usuario_id).id
        disco_id = Disco.query.filter_by(codigo="NR-POP-001").first().id

    client.post("/carrito/vaciar")
    client.post(f"/carrito/agregar/{disco_id}", data={"cantidad": 1})
    respuesta = client.post(
        "/checkout/confirmar",
        data={"metodo_pago_id": str(tarjeta_id)},
        follow_redirects=False,
    )
    assert respuesta.status_code == 302

    with app.app_context():
        return (
            Pedido.query.filter_by(cliente_id=usuario_id)
            .order_by(Pedido.id.desc())
            .first()
            .numero
        )


# ── Tests de generación directa con ReportLab ────────────────────────────────

def test_generar_pdf_comprobante_valido(client):
    with client:
        autenticar_cliente(client)
        numero = crear_pedido_cliente(client)
        with app.app_context():
            pedido = Pedido.query.filter_by(numero=numero).first()

            pdf_bytes, nombre_archivo, factura = generar_pdf_pedido(
                pedido, tipo="COMPROBANTE_PENDIENTE"
            )

        # Comprobar que es un PDF válido (comienza con %PDF-)
            assert pdf_bytes.startswith(b"%PDF-")
            assert len(pdf_bytes) > 500
            assert nombre_archivo.endswith(".pdf")
            assert "COMP-" in nombre_archivo

        # Comprobar persistencia de Factura
            assert factura is not None
            assert factura.tipo == "COMPROBANTE_PENDIENTE"
            assert factura.pedido_id == pedido.id


# ── Tests de descarga mediante endpoints HTTP ────────────────────────────────

def test_descargar_comprobante_cliente_autenticado(client):
    with client:
        autenticar_cliente(client)
        numero = crear_pedido_cliente(client)

        resp = client.get(f"/pedidos/{numero}/comprobante")
        assert resp.status_code == 200
        assert resp.mimetype == "application/pdf"
        assert f"COMP-{numero}.pdf" in resp.headers.get("Content-Disposition", "")
        assert resp.data.startswith(b"%PDF-")


def test_cliente_no_puede_descargar_comprobante_ajeno(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            admin = Usuario.query.filter_by(rol="administrador").first()
            tarjeta_admin = obtener_o_crear_tarjeta_verificada(admin.id)
            numero_ajeno = f"NR-PDF-{secrets.token_hex(4).upper()}"

            pedido_admin = Pedido(
                numero=numero_ajeno,
                cliente_id=admin.id,
                metodo_pago_id=tarjeta_admin.id,
                total=120.00,
                estado="PENDIENTE",
            )
            db.session.add(pedido_admin)
            db.session.commit()

        # El cliente no debe tener acceso al comprobante del admin
        resp = client.get(f"/pedidos/{numero_ajeno}/comprobante")
        assert resp.status_code == 404


def test_factura_final_bloqueada_si_no_esta_aprobado(client):
    with client:
        autenticar_cliente(client)
        numero = crear_pedido_cliente(client)

        resp = client.get(f"/pedidos/{numero}/factura", follow_redirects=True)
        assert resp.status_code == 200
        assert "Factura Oficial de venta solo está disponible" in resp.data.decode("utf-8")


def test_descargar_factura_final_cuando_aprobado(client):
    with client:
        autenticar_cliente(client)
        numero = crear_pedido_cliente(client)
        with app.app_context():
            pedido = Pedido.query.filter_by(numero=numero).first()
            # Simular aprobación del pedido
            pedido.estado = "APROBADO"
            db.session.commit()

        resp = client.get(f"/pedidos/{numero}/factura")
        assert resp.status_code == 200
        assert resp.mimetype == "application/pdf"
        assert f"FAC-{numero}.pdf" in resp.headers.get("Content-Disposition", "")
        assert resp.data.startswith(b"%PDF-")


# ── Tests de notificaciones ──────────────────────────────────────────────────

def test_notificaciones_ejecutan_sin_error(client):
    with client:
        autenticar_cliente(client)
        numero = crear_pedido_cliente(client)
        with app.app_context():
            pedido = Pedido.query.filter_by(numero=numero).first()

            # En modo dev retornan False limpiamente sin lanzar excepciones.
            resultado_creacion = notificar_creacion_pedido(pedido)
            assert resultado_creacion in (True, False)

            resultado_estado = notificar_cambio_estado(pedido)
            assert resultado_estado in (True, False)
