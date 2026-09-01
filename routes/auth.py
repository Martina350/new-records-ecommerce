"""Rutas de registro, autenticación y perfil."""

from email_validator import EmailNotValidError
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from auth import cerrar_sesion, iniciar_sesion, login_requerido, obtener_usuario_actual
from models import Usuario, db
from validators import (
    es_solicitud_ajax,
    es_url_segura,
    normalizar_email,
    validar_nombre_persona,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Registra una nueva cuenta pública asignando siempre el rol cliente."""
    es_ajax = es_solicitud_ajax()

    if "usuario_id" in session:
        usuario = obtener_usuario_actual()
        if usuario and usuario.es_administrador():
            dest = url_for("admin.admin_dashboard")
        else:
            dest = url_for("catalogo.productos")
        if es_ajax:
            return jsonify({"ok": True, "redirect": dest})
        return redirect(dest)

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmar_password = request.form.get("confirmar_password", "")

        errores = {}

        error_nombre = validar_nombre_persona(nombre)
        if error_nombre:
            errores["nombre"] = error_nombre

        if not email:
            errores["email"] = "El correo es un campo obligatorio."
        elif Usuario.query.filter_by(email=email).first() is not None:
            errores["email"] = (
                "Ya existe una cuenta registrada con este correo electrónico."
            )
        else:
            try:
                email_normalizado = normalizar_email(email)
                if len(email_normalizado) > 120:
                    errores["email"] = (
                        "El correo electrónico no puede superar 120 caracteres."
                    )
                elif (
                    Usuario.query.filter_by(email=email_normalizado).first() is not None
                ):
                    errores["email"] = (
                        "Ya existe una cuenta registrada con este correo electrónico."
                    )
                else:
                    email = email_normalizado
            except EmailNotValidError:
                errores["email"] = (
                    "El correo debe ser un correo válido. Introduce un correo electrónico válido."
                )

        if not password:
            errores["password"] = "La contraseña es un campo obligatorio."
        elif len(password) < 8:
            errores["password"] = (
                "La contraseña debe tener mínimo 8 caracteres (al menos 8 caracteres)."
            )

        if not confirmar_password:
            errores["confirmar_password"] = (
                "Confirmar contraseña es un campo obligatorio."
            )
        elif password and password != confirmar_password:
            errores["confirmar_password"] = (
                "La contraseña debe coincidir (Las contraseñas no coinciden)."
            )

        if errores:
            if es_ajax:
                return jsonify({"ok": False, "errores": errores}), 400
            return render_template(
                "auth/registro.html",
                nombre=nombre,
                email=email,
                errores=errores,
            )

        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            rol="cliente",
            activo=True,
        )
        nuevo_usuario.set_password(password)

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash(
                "¡Tu cuenta ha sido creada exitosamente! Ahora puedes iniciar sesión.",
                "success",
            )
            if es_ajax:
                return jsonify({"ok": True, "redirect": url_for("auth.login")}), 200
            return redirect(url_for("auth.login"))
        except Exception:
            db.session.rollback()
            errores["general"] = (
                "Ocurrió un error al procesar el registro. Inténtalo más tarde."
            )
            if es_ajax:
                return jsonify({"ok": False, "errores": errores}), 500
            return render_template(
                "auth/registro.html", nombre=nombre, email=email, errores=errores
            )

    return render_template("auth/registro.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Inicia la sesión del usuario previa verificación de credenciales."""
    es_ajax = es_solicitud_ajax()

    if "usuario_id" in session:
        usuario = obtener_usuario_actual()
        if usuario and usuario.es_administrador():
            dest = url_for("admin.admin_dashboard")
        else:
            dest = url_for("catalogo.productos")
        if es_ajax:
            return jsonify({"ok": True, "redirect": dest})
        return redirect(dest)

    next_url = request.args.get("next")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        errores = {}

        if not email:
            errores["email"] = "El correo electrónico es un campo obligatorio."
        if not password:
            errores["password"] = "La contraseña es un campo obligatorio."

        if errores:
            if es_ajax:
                return jsonify({"ok": False, "errores": errores}), 400
            return render_template(
                "auth/login.html", email=email, next=next_url, errores=errores
            )

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario is None or not usuario.check_password(password):
            errores["password"] = "Correo electrónico o contraseña incorrectos."
            errores["general"] = "Correo electrónico o contraseña incorrectos."
            if es_ajax:
                return jsonify({"ok": False, "errores": errores}), 400
            return render_template(
                "auth/login.html", email=email, next=next_url, errores=errores
            )

        if not usuario.activo:
            errores["password"] = (
                "Esta cuenta se encuentra desactivada. Contacta al administrador."
            )
            errores["general"] = (
                "Esta cuenta se encuentra desactivada. Contacta al administrador."
            )
            if es_ajax:
                return jsonify({"ok": False, "errores": errores}), 400
            return render_template(
                "auth/login.html", email=email, next=next_url, errores=errores
            )

        iniciar_sesion(usuario)
        flash(f"¡Bienvenido de nuevo, {usuario.nombre}!", "success")

        if next_url and es_url_segura(next_url):
            dest = next_url
        elif usuario.es_administrador():
            dest = url_for("admin.admin_dashboard")
        else:
            dest = url_for("catalogo.productos")

        if es_ajax:
            return jsonify({"ok": True, "redirect": dest}), 200

        return redirect(dest)

    return render_template("auth/login.html", next=next_url)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Cierra la sesión activa del usuario."""
    cerrar_sesion()
    flash("Has cerrado sesión correctamente. ¡Hasta pronto!", "info")
    return redirect(url_for("catalogo.inicio"))


@auth_bp.route("/perfil", methods=["GET", "POST"])
@login_requerido
def perfil():
    """Muestra y permite actualizar la información del perfil del usuario autenticado."""
    usuario = obtener_usuario_actual()
    if usuario is None:
        cerrar_sesion()
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        ciudad = request.form.get("ciudad", "").strip()

        error_nombre = validar_nombre_persona(nombre)
        if error_nombre:
            flash(error_nombre, "error")
            return render_template("auth/perfil.html", usuario=usuario)

        if len(telefono) > 20 or len(direccion) > 200 or len(ciudad) > 100:
            flash("Uno de los datos del perfil supera la longitud permitida.", "error")
            return render_template("auth/perfil.html", usuario=usuario)

        usuario.nombre = nombre
        usuario.telefono = telefono or None
        usuario.direccion = direccion or None
        usuario.ciudad = ciudad or None

        session["usuario_nombre"] = usuario.nombre

        try:
            db.session.commit()
            flash("Tu perfil ha sido actualizado correctamente.", "success")
            return redirect(url_for("auth.perfil"))
        except Exception:
            db.session.rollback()
            flash("Error al actualizar el perfil. Inténtalo de nuevo.", "error")

    return render_template("auth/perfil.html", usuario=usuario)
