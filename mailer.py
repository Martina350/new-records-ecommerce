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
