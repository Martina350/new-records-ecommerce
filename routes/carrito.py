"""Rutas del carrito temporal del cliente."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from auth import rol_requerido
from cart import (
    actualizar_cantidad,
    agregar_disco,
    eliminar_disco,
    obtener_detalle_carrito,
    vaciar_carrito,
)
from validators import es_url_segura

carrito_bp = Blueprint("carrito", __name__)


@carrito_bp.route("/carrito")
@rol_requerido("cliente")
def ver_carrito():
    """Muestra los productos del carrito con subtotales polimórficos y total general."""
    detalle_carrito = obtener_detalle_carrito()
    return render_template("carrito.html", carrito=detalle_carrito)


@carrito_bp.route("/carrito/agregar/<int:disco_id>", methods=["POST"])
@rol_requerido("cliente")
def agregar_al_carrito(disco_id):
    """Agrega un disco al carrito o incrementa su cantidad."""
    try:
        cantidad = int(request.form.get("cantidad", 1))
    except (ValueError, TypeError):
        cantidad = 1

    if cantidad < 1:
        cantidad = 1

    agregar_disco(disco_id, cantidad=cantidad)

    # Redirigir a la página de origen si existe y es segura, o al carrito
    referrer = request.referrer
    if referrer and es_url_segura(referrer):
        return redirect(referrer)
    return redirect(url_for("carrito.ver_carrito"))


@carrito_bp.route("/carrito/actualizar/<int:disco_id>", methods=["POST"])
@rol_requerido("cliente")
def actualizar_carrito(disco_id):
    """Actualiza la cantidad solicitada para un disco del carrito."""
    try:
        cantidad = int(request.form.get("cantidad", 1))
    except (ValueError, TypeError):
        cantidad = 1

    actualizar_cantidad(disco_id, cantidad)
    return redirect(url_for("carrito.ver_carrito"))


@carrito_bp.route("/carrito/eliminar/<int:disco_id>", methods=["POST"])
@rol_requerido("cliente")
def eliminar_del_carrito(disco_id):
    """Remueve un disco del carrito."""
    eliminar_disco(disco_id)
    return redirect(url_for("carrito.ver_carrito"))


@carrito_bp.route("/carrito/vaciar", methods=["POST"])
@rol_requerido("cliente")
def vaciar_carrito_ruta():
    """Vacía completamente el carrito."""
    vaciar_carrito()
    flash("Se vació el carrito correctamente.", "info")
    return redirect(url_for("carrito.ver_carrito"))
