"""Módulo de autenticación, sesiones y autorización por roles para New Records."""

from functools import wraps

from flask import abort, flash, redirect, request, session, url_for

from models import Usuario, db


def login_requerido(vista):
    """Exige que exista un usuario autenticado en la sesión activa."""

    @wraps(vista)
    def vista_decorada(*args, **kwargs):
        if obtener_usuario_actual() is None:
            flash(
                "Debes iniciar sesión para acceder a esta página.", "warning"
            )
            return redirect(url_for("login", next=request.full_path))
        return vista(*args, **kwargs)

    return vista_decorada


def rol_requerido(*roles_permitidos):
    """Exige que el usuario autenticado posea uno de los roles autorizados."""

    def decorador(vista):
        @wraps(vista)
        def vista_decorada(*args, **kwargs):
            usuario = obtener_usuario_actual()
            if usuario is None:
                flash(
                    "Debes iniciar sesión para acceder a esta página.",
                    "warning",
                )
                return redirect(url_for("login", next=request.full_path))

            if usuario.rol not in roles_permitidos:
                abort(403)

            return vista(*args, **kwargs)

        return vista_decorada

    return decorador


def iniciar_sesion(usuario):
    """Registra los datos mínimos indispensables del usuario en la sesión de Flask."""
    session.clear()
    session["usuario_id"] = usuario.id
    session["usuario_nombre"] = usuario.nombre
    session["usuario_rol"] = usuario.rol


def cerrar_sesion():
    """Limpia completamente la sesión activa."""
    session.clear()


def obtener_usuario_actual():
    """Retorna la instancia del usuario autenticado o None si no hay sesión."""
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return None
    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        session.clear()
        return None

    session["usuario_nombre"] = usuario.nombre
    session["usuario_rol"] = usuario.rol
    return usuario
