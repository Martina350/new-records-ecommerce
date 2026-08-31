"""Rutas de checkout, historial, detalle y documentos de pedidos."""

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from auth import login_requerido, obtener_usuario_actual, rol_requerido
from cart import obtener_detalle_carrito
from mailer import notificar_creacion_pedido
from models import db
from payments import obtener_metodos_pago_activos
from pdf_generator import generar_pdf_pedido
from services import (
    obtener_pedido_por_numero,
    obtener_pedidos_cliente,
    procesar_checkout,
)

pedidos_bp = Blueprint("pedidos", __name__)


@pedidos_bp.route("/checkout/resumen")
@rol_requerido("cliente")
def checkout_resumen():
    """Muestra el resumen previo del pedido antes del pago y confirmación."""
    detalle_carrito = obtener_detalle_carrito()

    if not detalle_carrito["elementos"]:
        flash(
            "Tu carrito está vacío. Agrega productos antes de ir al checkout.",
            "warning",
        )
        return redirect(url_for("carrito.ver_carrito"))

    usuario = obtener_usuario_actual()
    metodos_pago = obtener_metodos_pago_activos(usuario.id)
    return render_template(
        "checkout_resumen.html",
        carrito=detalle_carrito,
        usuario=usuario,
        metodos_pago=metodos_pago,
    )


@pedidos_bp.route("/checkout/confirmar", methods=["POST"])
@rol_requerido("cliente")
def confirmar_checkout():
    """Procesa el checkout y crea el pedido persistente con cobro simulado."""
    metodo_pago_id = request.form.get("metodo_pago_id")
    if not metodo_pago_id:
        flash("Debes seleccionar un método de pago verificado para continuar.", "error")
        return redirect(url_for("pedidos.checkout_resumen"))

    try:
        metodo_id_int = int(metodo_pago_id)
    except (ValueError, TypeError):
        flash("Método de pago inválido.", "error")
        return redirect(url_for("pedidos.checkout_resumen"))

    exito, resultado = procesar_checkout(session["usuario_id"], metodo_id_int)
    if exito:
        # Enviar notificación por correo (si SMTP está configurado)
        notificar_creacion_pedido(resultado)
        flash(
            f"¡Tu pedido {resultado.numero} ha sido creado con éxito! Se encuentra pendiente de revisión.",
            "success",
        )
        return redirect(url_for("pedidos.ver_pedido", numero=resultado.numero))
    else:
        flash(resultado, "error")
        return redirect(url_for("pedidos.checkout_resumen"))


@pedidos_bp.route("/pedidos")
@rol_requerido("cliente")
def lista_pedidos():
    """Muestra el historial de pedidos realizados por el cliente autenticado."""
    pedidos = obtener_pedidos_cliente(session["usuario_id"])
    return render_template("pedidos/lista.html", pedidos=pedidos)


@pedidos_bp.route("/pedidos/<numero>")
@login_requerido
def ver_pedido(numero):
    """Muestra el detalle completo de un pedido específico."""
    usuario = obtener_usuario_actual()
    pedido = obtener_pedido_por_numero(numero, usuario)
    if not pedido:
        return render_template("errors/404.html"), 404

    return render_template("pedidos/detalle.html", pedido=pedido)


@pedidos_bp.route("/pedidos/<numero>/comprobante")
@login_requerido
def descargar_comprobante(numero):
    """Genera y transmite el comprobante de pedido en formato PDF."""
    usuario = obtener_usuario_actual()
    pedido = obtener_pedido_por_numero(numero, usuario)
    if not pedido:
        return render_template("errors/404.html"), 404

    try:
        pdf_bytes, nombre_archivo, _ = generar_pdf_pedido(
            pedido, tipo="COMPROBANTE_PENDIENTE"
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("No se pudo generar el comprobante. Inténtalo nuevamente.", "error")
        return redirect(url_for("pedidos.ver_pedido", numero=numero))
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={nombre_archivo}"},
    )


@pedidos_bp.route("/pedidos/<numero>/factura")
@login_requerido
def descargar_factura(numero):
    """Genera y transmite la factura final de venta en formato PDF tras aprobación."""
    usuario = obtener_usuario_actual()
    pedido = obtener_pedido_por_numero(numero, usuario)
    if not pedido:
        return render_template("errors/404.html"), 404

    if pedido.estado != "APROBADO":
        flash(
            "La Factura Oficial de venta solo está disponible una vez que el pedido haya sido APROBADO.",
            "warning",
        )
        return redirect(url_for("pedidos.ver_pedido", numero=numero))

    try:
        pdf_bytes, nombre_archivo, _ = generar_pdf_pedido(pedido, tipo="FACTURA_FINAL")
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("No se pudo generar la factura. Inténtalo nuevamente.", "error")
        return redirect(url_for("pedidos.ver_pedido", numero=numero))
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={nombre_archivo}"},
    )
