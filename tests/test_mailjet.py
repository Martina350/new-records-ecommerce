"""Pruebas de configuración SMTP y destinatarios de correo."""

from types import SimpleNamespace
from unittest.mock import patch

from app import app
from mailer import (
    enviar_pin,
    mail,
    notificar_cambio_estado,
    notificar_creacion_pedido,
    smtp_configurado,
)


CONFIGURACION_VALIDA = {
    "MAIL_SERVER": "in-v3.mailjet.com",
    "MAIL_PORT": 587,
    "MAIL_USE_TLS": True,
    "MAIL_USE_SSL": False,
    "MAIL_DEBUG": False,
    "MAIL_USERNAME": "api_key_de_prueba",
    "MAIL_PASSWORD": "secret_key_de_prueba",
    "MAIL_DEFAULT_SENDER": "ventas@dominio-validado.com",
}


def test_valores_de_ejemplo_no_activan_el_envio():
    with app.app_context():
        with patch.dict(
            app.config,
            {
                "MAIL_SERVER": "in-v3.mailjet.com",
                "MAIL_USERNAME": "your_mailjet_api_key",
                "MAIL_PASSWORD": "your_mailjet_secret_key",
                "MAIL_DEFAULT_SENDER": "ventas@newrecords.example",
            },
        ):
            assert smtp_configurado() is False


def test_configuracion_mailjet_completa_activa_el_envio():
    with app.app_context():
        with patch.dict(app.config, CONFIGURACION_VALIDA):
            assert smtp_configurado() is True


def test_pin_se_dirige_al_correo_del_cliente():
    with app.app_context():
        with patch.dict(app.config, CONFIGURACION_VALIDA), patch.object(mail, "send") as enviar:
            assert enviar_pin(
                "cliente-real@example.org",
                "Martina",
                "123456",
                "https://newrecords.example/pago/verificar/token",
            ) is True

            mensaje = enviar.call_args.args[0]
            assert mensaje.recipients == ["cliente-real@example.org"]
            assert "123456" in mensaje.body
            assert "Verificar mi tarjeta" in mensaje.html
            assert "123456" in mensaje.html


def test_confirmacion_de_pedido_se_dirige_al_cliente():
    pedido = SimpleNamespace(
        numero="NR-TEST-001",
        total=25.50,
        cliente=SimpleNamespace(nombre="Martina", email="cliente-real@example.org"),
    )

    with app.app_context():
        with patch.dict(app.config, CONFIGURACION_VALIDA), patch.object(mail, "send") as enviar:
            assert notificar_creacion_pedido(pedido) is True

            mensaje = enviar.call_args.args[0]
            assert mensaje.recipients == ["cliente-real@example.org"]
            assert pedido.numero in mensaje.subject
            assert "PENDIENTE DE REVISIÓN" in mensaje.html
            assert "$25.50" in mensaje.html


def test_cambio_de_estado_utiliza_la_plantilla_correspondiente():
    pedido = SimpleNamespace(
        numero="NR-TEST-002",
        estado="APROBADO",
        motivo_rechazo=None,
        cliente=SimpleNamespace(nombre="Martina", email="cliente-real@example.org"),
    )

    with app.app_context():
        with patch.dict(app.config, CONFIGURACION_VALIDA), patch.object(mail, "send") as enviar:
            assert notificar_cambio_estado(pedido) is True
            assert "APROBADO" in enviar.call_args.args[0].html
            assert "factura oficial" in enviar.call_args.args[0].html.lower()

            pedido.estado = "RECHAZADO"
            pedido.motivo_rechazo = "Producto sin disponibilidad."
            assert notificar_cambio_estado(pedido) is True
            assert "RECHAZADO" in enviar.call_args.args[0].html
            assert "Producto sin disponibilidad." in enviar.call_args.args[0].html
