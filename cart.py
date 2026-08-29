"""Módulo de gestión del carrito de compras basado en la sesión de Flask."""

from flask import flash, session

from models import Disco, db


def obtener_carrito_sesion():
    """Recupera el carrito de la sesión o lo inicializa como un diccionario vacío."""
    if "carrito" not in session or not isinstance(session["carrito"], dict):
        session["carrito"] = {}
    return session["carrito"]


def guardar_carrito_sesion(carrito):
    """Reasigna el carrito a la sesión y fuerza la marca de modificación."""
    session["carrito"] = carrito
    session.modified = True


def agregar_disco(disco_id, cantidad=1):
    """Agrega un disco al carrito o incrementa su cantidad validando el stock disponible."""
    if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad < 1:
        flash("La cantidad solicitada no es válida.", "error")
        return False

    disco = db.session.get(Disco, disco_id)
    if not disco or not disco.activo:
        flash("El disco seleccionado no está disponible.", "error")
        return False

    if disco.stock <= 0:
        flash(f"El disco '{disco.album}' se encuentra agotado.", "warning")
        return False

    carrito = obtener_carrito_sesion()
    clave_id = str(disco_id)
    cantidad_actual = carrito.get(clave_id, 0)
    if (
        isinstance(cantidad_actual, bool)
        or not isinstance(cantidad_actual, int)
        or cantidad_actual < 0
    ):
        cantidad_actual = 0
    nueva_cantidad = cantidad_actual + cantidad

    if nueva_cantidad > disco.stock:
        nueva_cantidad = disco.stock
        flash(
            f"Se ajustó la cantidad al máximo de stock disponible ({disco.stock} unidades).",
            "warning",
        )
    else:
        flash(f"Se agregó '{disco.album}' al carrito.", "success")

    carrito[clave_id] = nueva_cantidad
    guardar_carrito_sesion(carrito)
    return True


def actualizar_cantidad(disco_id, cantidad):
    """Actualiza la cantidad de un disco en el carrito o lo remueve si es <= 0."""
    carrito = obtener_carrito_sesion()
    clave_id = str(disco_id)

    if clave_id not in carrito:
        return False

    if cantidad <= 0:
        return eliminar_disco(disco_id)

    disco = db.session.get(Disco, disco_id)
    if not disco or not disco.activo:
        return eliminar_disco(disco_id)

    if disco.stock <= 0:
        flash(f"El disco '{disco.album}' se encuentra agotado.", "warning")
        return eliminar_disco(disco_id)

    if cantidad > disco.stock:
        cantidad = disco.stock
        flash(
            f"Cantidad ajustada al stock disponible de '{disco.album}' ({disco.stock} unidades).",
            "warning",
        )

    carrito[clave_id] = cantidad
    guardar_carrito_sesion(carrito)
    return True


def eliminar_disco(disco_id):
    """Elimina un disco del carrito de la sesión."""
    carrito = obtener_carrito_sesion()
    clave_id = str(disco_id)
    if clave_id in carrito:
        del carrito[clave_id]
        guardar_carrito_sesion(carrito)
        flash("Producto eliminado del carrito.", "info")
        return True
    return False


def vaciar_carrito():
    """Vacía completamente el carrito."""
    session["carrito"] = {}
    session.modified = True


def obtener_detalle_carrito():
    """Consulta la BD PostgreSQL, revalida stock y calcula subtotales polimórficos y total general."""
    carrito = obtener_carrito_sesion()
    items = []
    total_general = 0
    total_unidades = 0
    carrito_modificado = False
    claves_a_eliminar = []

    for clave_id, cantidad in list(carrito.items()):
        if (
            isinstance(cantidad, bool)
            or not isinstance(cantidad, int)
            or cantidad < 1
        ):
            claves_a_eliminar.append(clave_id)
            carrito_modificado = True
            continue

        try:
            disco_id = int(clave_id)
        except ValueError:
            claves_a_eliminar.append(clave_id)
            carrito_modificado = True
            continue

        disco = db.session.get(Disco, disco_id)
        if not disco or not disco.activo or disco.stock <= 0:
            claves_a_eliminar.append(clave_id)
            carrito_modificado = True
            continue

        # Si el stock disminuyó por debajo de la cantidad pedida, se ajusta
        if cantidad > disco.stock:
            cantidad = disco.stock
            carrito[clave_id] = cantidad
            carrito_modificado = True

        precio_unitario = disco.precio_final()
        subtotal = precio_unitario * cantidad

        items.append(
            {
                "disco": disco,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal,
            }
        )

        total_general += subtotal
        total_unidades += cantidad

    for clave in claves_a_eliminar:
        carrito.pop(clave, None)

    if carrito_modificado:
        guardar_carrito_sesion(carrito)

    return {
        "elementos": items,
        "total_general": total_general,
        "total_unidades": total_unidades,
    }
