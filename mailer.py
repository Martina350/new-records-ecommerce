"""Servicio central de correo para los mensajes enviados por New Records."""

from flask import current_app, has_app_context, has_request_context, url_for
from flask_mail import Mail, Message

mail = Mail()


def _es_valor_real(valor):
    """Descarta valores vacíos y marcadores incluidos en archivos de ejemplo."""
    if not valor:
        return False

    normalizado = str(valor).strip().lower()
    marcadores = (
        "change_",
        "your_",
        "tu_",
        "<",
        "smtp.example.com",
        "@newrecords.example",
        "@newrecords.local",
    )
    return not any(marcador in normalizado for marcador in marcadores)


def smtp_configurado():
    """Indica si el proveedor SMTP tiene credenciales y remitente reales."""
    if not has_app_context():
        return False

    claves_requeridas = (
        "MAIL_SERVER",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "MAIL_DEFAULT_SENDER",
    )
    return all(
        _es_valor_real(current_app.config.get(clave)) for clave in claves_requeridas
    )


def _url_pedidos():
    """Genera el enlace al historial cuando existe una solicitud web activa."""
    if not has_request_context():
        return None
    return url_for("pedidos.lista_pedidos", _external=True)


def _enviar_mensaje(asunto, destinatario, cuerpo, plantilla, **contexto):
    """Envía un mensaje y registra el fallo sin exponer credenciales al usuario."""
    if not smtp_configurado():
        return False

    try:
        contenido_html = current_app.jinja_env.get_or_select_template(plantilla).render(
            **contexto
        )
        mensaje = Message(
            subject=asunto,
            recipients=[destinatario],
            body=cuerpo,
            html=contenido_html,
        )
        mail.send(mensaje)
        return True
    except Exception:
        current_app.logger.exception(
            "No fue posible enviar el correo '%s' al destinatario solicitado.",
            asunto,
        )
        return False


def enviar_pin(destinatario, nombre, pin, url_verificacion=None):
    """Envía el PIN de verificación al correo del cliente."""
    asunto = "New Records — Tu código de verificación de tarjeta"
    cuerpo = (
        f"Hola {nombre},\n\n"
        f"Tu código de verificación para confirmar tu tarjeta en New Records es:\n\n"
        f"    {pin}\n\n"
        "Este código es válido por 5 minutos. "
        "Si no realizaste esta solicitud, ignora este mensaje.\n\n"
        "— Equipo New Records"
    )
    return _enviar_mensaje(
        asunto,
        destinatario,
        cuerpo,
        "emails/pin_verificacion.html",
        nombre=nombre,
        pin=pin,
        url_verificacion=url_verificacion,
    )


def notificar_creacion_pedido(pedido):
    """Envía al cliente la confirmación de que su pedido fue recibido."""
    cliente = pedido.cliente
    asunto = f"New Records — Pedido {pedido.numero} recibido con éxito"
    cuerpo = (
        f"Hola {cliente.nombre},\n\n"
        f"Hemos recibido tu pedido {pedido.numero} con un total de ${pedido.total:.2f}.\n\n"
        "Tu orden se encuentra actualmente en estado PENDIENTE de revisión administrativa. "
        "Te notificaremos en cuanto sea aprobada para proceder al despacho.\n\n"
        "Puedes consultar tu comprobante y el detalle de tu compra ingresando "
        "a tu cuenta en New Records.\n\n"
        "— Equipo New Records"
    )
    return _enviar_mensaje(
        asunto,
        cliente.email,
        cuerpo,
        "emails/pedido_recibido.html",
        nombre=cliente.nombre,
        numero=pedido.numero,
        total=f"{pedido.total:.2f}",
        url_pedidos=_url_pedidos(),
    )


def notificar_cambio_estado(pedido):
    """Notifica al cliente la aprobación o el rechazo de su pedido."""
    cliente = pedido.cliente
    asunto = f"New Records — Actualización de tu pedido {pedido.numero}"

    if pedido.estado == "APROBADO":
        cuerpo = (
            f"Hola {cliente.nombre},\n\n"
            f"¡Buenas noticias! Tu pedido {pedido.numero} ha sido APROBADO.\n"
            "Ya puedes descargar tu Factura Oficial de venta desde tu panel de pedidos.\n\n"
            "— Equipo New Records"
        )
    else:
        cuerpo = (
            f"Hola {cliente.nombre},\n\n"
            f"Te informamos que tu pedido {pedido.numero} ha sido RECHAZADO.\n"
            f"Motivo: {pedido.motivo_rechazo or 'Sin motivo especificado'}.\n\n"
            "— Equipo New Records"
        )

    plantilla = (
        "emails/pedido_aprobado.html"
        if pedido.estado == "APROBADO"
        else "emails/pedido_rechazado.html"
    )
    return _enviar_mensaje(
        asunto,
        cliente.email,
        cuerpo,
        plantilla,
        nombre=cliente.nombre,
        numero=pedido.numero,
        motivo=pedido.motivo_rechazo or "Sin motivo especificado",
        url_pedidos=_url_pedidos(),
    )
