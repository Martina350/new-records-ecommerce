"""Servicio de correo electrónico para el envío de PINes de verificación en New Records."""

import os

from flask_mail import Mail, Message

mail = Mail()


def smtp_configurado():
    """Devuelve True solo si las variables de entorno SMTP están configuradas con valores reales."""
    servidor = os.getenv("MAIL_SERVER", "")
    usuario = os.getenv("MAIL_USERNAME", "")
    return bool(servidor and servidor != "smtp.example.com" and usuario and usuario != "your_email@example.com")


def enviar_pin(destinatario, nombre, pin):
    """Envía el PIN de verificación al correo del cliente.

    Retorna True si el correo fue enviado, False si falló o SMTP no está configurado.
    """
    if not smtp_configurado():
        return False

    try:
        asunto = "New Records — Tu código de verificación de tarjeta"
        cuerpo = (
            f"Hola {nombre},\n\n"
            f"Tu código de verificación para confirmar tu tarjeta en New Records es:\n\n"
            f"    {pin}\n\n"
            f"Este código es válido por 5 minutos. Si no realizaste esta solicitud, ignora este mensaje.\n\n"
            f"— Equipo New Records"
        )
        msg = Message(subject=asunto, recipients=[destinatario], body=cuerpo)
        mail.send(msg)
        return True
    except Exception:
        return False


def notificar_creacion_pedido(pedido):
    """Envía un correo de confirmación de pedido recibido al cliente."""
    if not smtp_configurado():
        return False

    try:
        cliente = pedido.cliente
        asunto = f"New Records — Pedido {pedido.numero} recibido con éxito"
        cuerpo = (
            f"Hola {cliente.nombre},\n\n"
            f"Hemos recibido tu pedido {pedido.numero} con un total de ${pedido.total:.2f}.\n\n"
            f"Tu orden se encuentra actualmente en estado PENDIENTE de revisión administrativa. "
            f"Te notificaremos en cuanto sea aprobada para proceder al despacho.\n\n"
            f"Puedes consultar tu comprobante y el detalle de tu compra ingresando a tu cuenta en New Records.\n\n"
            f"— Equipo New Records"
        )
        msg = Message(subject=asunto, recipients=[cliente.email], body=cuerpo)
        mail.send(msg)
        return True
    except Exception:
        return False


def notificar_cambio_estado(pedido):
    """Envía un correo al cliente notificando la aprobación o rechazo de su pedido."""
    if not smtp_configurado():
        return False

    try:
        cliente = pedido.cliente
        asunto = f"New Records — Actualización de tu pedido {pedido.numero}"
        if pedido.estado == "APROBADO":
            cuerpo = (
                f"Hola {cliente.nombre},\n\n"
                f"¡Buenas noticias! Tu pedido {pedido.numero} ha sido APROBADO.\n"
                f"Ya puedes descargar tu Factura Oficial de venta desde tu panel de pedidos.\n\n"
                f"— Equipo New Records"
            )
        else:
            cuerpo = (
                f"Hola {cliente.nombre},\n\n"
                f"Te informamos que tu pedido {pedido.numero} ha sido RECHAZADO.\n"
                f"Motivo: {pedido.motivo_rechazo or 'Sin motivo especificado'}.\n\n"
                f"— Equipo New Records"
            )
        msg = Message(subject=asunto, recipients=[cliente.email], body=cuerpo)
        mail.send(msg)
        return True
    except Exception:
        return False
