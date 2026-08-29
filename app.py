"""Punto de entrada de la aplicación New Records."""

import click
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import urlsplit

from auth import (
    cerrar_sesion,
    iniciar_sesion,
    login_requerido,
    obtener_usuario_actual,
    rol_requerido,
)
from cart import (
    actualizar_cantidad,
    agregar_disco,
    eliminar_disco,
    obtener_carrito_sesion,
    obtener_detalle_carrito,
    vaciar_carrito,
)
from config import Config
from models import Categoria, Disco, Usuario, db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


def es_url_segura(destino):
    """Verifica que la redirección sea interna y no apunte a dominios externos."""
    if not destino:
        return False
    ref_host = urlsplit(request.host_url).netloc
    test_host = urlsplit(destino).netloc
    return not test_host or test_host == ref_host


@app.context_processor
def inyectar_contexto_usuario():
    """Inyecta el usuario actual, su estado y el contador de ítems del carrito en todas las plantillas."""
    carrito = obtener_carrito_sesion()
    total_items = sum(cantidad for cantidad in carrito.values() if isinstance(cantidad, int))
    return {
        "usuario_actual": obtener_usuario_actual(),
        "esta_autenticado": "usuario_id" in session,
        "es_admin": session.get("usuario_rol") == "administrador",
        "total_items_carrito": total_items,
    }


@app.route("/")
def inicio():
    """Muestra la portada de New Records."""
    return render_template("index.html")


@app.route("/categorias")
def categorias():
    """Muestra las categorías musicales activas desde PostgreSQL."""
    lista_categorias = (
        Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    )
    return render_template("categorias.html", categorias=lista_categorias)


@app.route("/productos")
def productos():
    """Muestra el catálogo dinámico de discos con filtros por categoría y búsqueda."""
    categoria_slug = request.args.get("categoria", "").strip()
    busqueda = request.args.get("q", "").strip()

    consulta = Disco.query.filter_by(activo=True)

    categoria_actual = None
    if categoria_slug and categoria_slug != "todos":
        categoria_actual = Categoria.query.filter_by(
            slug=categoria_slug, activo=True
        ).first()
        if categoria_actual:
            consulta = consulta.filter_by(categoria_id=categoria_actual.id)

    if busqueda:
        termino = f"%{busqueda}%"
        consulta = consulta.filter(
            db.or_(Disco.album.ilike(termino), Disco.artista.ilike(termino))
        )

    lista_discos = consulta.order_by(Disco.album).all()
    lista_categorias = (
        Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    )

    return render_template(
        "productos.html",
        discos=lista_discos,
        categorias=lista_categorias,
        categoria_actual=categoria_actual,
        categoria_slug=categoria_slug or "todos",
        busqueda=busqueda,
    )


@app.route("/productos/<codigo>")
def detalle_producto(codigo):
    """Muestra la ficha técnica polimórfica de un disco y recomendaciones de la misma categoría."""
    disco = Disco.query.filter_by(codigo=codigo, activo=True).first_or_404()

    recomendados = (
        Disco.query.filter(
            Disco.categoria_id == disco.categoria_id,
            Disco.id != disco.id,
            Disco.activo.is_(True),
        )
        .order_by(Disco.album)
        .limit(4)
        .all()
    )

    return render_template(
        "detalle_producto.html",
        disco=disco,
        recomendados=recomendados,
    )


@app.route("/contacto")
def contacto():
    """Muestra el formulario de contacto del prototipo."""
    return render_template("contacto.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    """Registra una nueva cuenta pública asignando siempre el rol cliente."""
    if "usuario_id" in session:
        return redirect(url_for("inicio"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmar_password = request.form.get("confirmar_password", "")

        if not nombre or not email or not password:
            flash("Todos los campos obligatorios deben ser completados.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

        if password != confirmar_password:
            flash("Las contraseñas no coinciden. Inténtalo de nuevo.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

        if Usuario.query.filter_by(email=email).first() is not None:
            flash("Ya existe una cuenta registrada con este correo electrónico.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

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
            flash("¡Tu cuenta ha sido creada exitosamente! Ahora puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        except Exception:
            db.session.rollback()
            flash("Ocurrió un error al procesar el registro. Inténtalo más tarde.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

    return render_template("auth/registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicia la sesión del usuario previa verificación de credenciales."""
    if "usuario_id" in session:
        return redirect(url_for("inicio"))

    next_url = request.args.get("next")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario is None or not usuario.check_password(password):
            flash("Correo electrónico o contraseña incorrectos.", "error")
            return render_template("auth/login.html", email=email, next=next_url)

        if not usuario.activo:
            flash("Esta cuenta se encuentra desactivada. Contacta al administrador.", "error")
            return render_template("auth/login.html", email=email, next=next_url)

        iniciar_sesion(usuario)
        flash(f"¡Bienvenido de nuevo, {usuario.nombre}!", "success")

        if next_url and es_url_segura(next_url):
            return redirect(next_url)

        if usuario.es_administrador():
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("inicio"))

    return render_template("auth/login.html", next=next_url)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """Cierra la sesión activa del usuario."""
    cerrar_sesion()
    flash("Has cerrado sesión correctamente. ¡Hasta pronto!", "info")
    return redirect(url_for("inicio"))


@app.route("/perfil", methods=["GET", "POST"])
@login_requerido
def perfil():
    """Muestra y permite actualizar la información del perfil del usuario autenticado."""
    usuario = obtener_usuario_actual()
    if usuario is None:
        cerrar_sesion()
        return redirect(url_for("login"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        ciudad = request.form.get("ciudad", "").strip()

        if not nombre:
            flash("El nombre completo es obligatorio.", "error")
            return render_template("auth/perfil.html", usuario=usuario)

        usuario.nombre = nombre
        usuario.telefono = telefono or None
        usuario.direccion = direccion or None
        usuario.ciudad = ciudad or None

        session["usuario_nombre"] = usuario.nombre

        try:
            db.session.commit()
            flash("Tu perfil ha sido actualizado correctamente.", "success")
            return redirect(url_for("perfil"))
        except Exception:
            db.session.rollback()
            flash("Error al actualizar el perfil. Inténtalo de nuevo.", "error")

    return render_template("auth/perfil.html", usuario=usuario)


@app.route("/carrito")
@login_requerido
def ver_carrito():
    """Muestra los productos del carrito con subtotales polimórficos y total general."""
    detalle_carrito = obtener_detalle_carrito()
    return render_template("carrito.html", carrito=detalle_carrito)


@app.route("/carrito/agregar/<int:disco_id>", methods=["POST"])
@login_requerido
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
    return redirect(url_for("ver_carrito"))


@app.route("/carrito/actualizar/<int:disco_id>", methods=["POST"])
@login_requerido
def actualizar_carrito(disco_id):
    """Actualiza la cantidad solicitada para un disco del carrito."""
    try:
        cantidad = int(request.form.get("cantidad", 1))
    except (ValueError, TypeError):
        cantidad = 1

    actualizar_cantidad(disco_id, cantidad)
    return redirect(url_for("ver_carrito"))


@app.route("/carrito/eliminar/<int:disco_id>", methods=["POST"])
@login_requerido
def eliminar_del_carrito(disco_id):
    """Remueve un disco del carrito."""
    eliminar_disco(disco_id)
    return redirect(url_for("ver_carrito"))


@app.route("/carrito/vaciar", methods=["POST"])
@login_requerido
def vaciar_carrito_ruta():
    """Vacía completamente el carrito."""
    vaciar_carrito()
    flash("Se vació el carrito correctamente.", "info")
    return redirect(url_for("ver_carrito"))


@app.route("/checkout/resumen")
@login_requerido
def checkout_resumen():
    """Muestra el resumen previo del pedido antes del pago y confirmación."""
    detalle_carrito = obtener_detalle_carrito()

    if not detalle_carrito["elementos"]:
        flash("Tu carrito está vacío. Agrega productos antes de ir al checkout.", "warning")
        return redirect(url_for("ver_carrito"))

    usuario = obtener_usuario_actual()
    return render_template(
        "checkout_resumen.html",
        carrito=detalle_carrito,
        usuario=usuario,
    )


@app.route("/admin/dashboard")
@rol_requerido("administrador")
def admin_dashboard():
    """Panel de administración restringido exclusivamente a administradores."""
    return render_template("admin/dashboard.html")


@app.errorhandler(403)
def acceso_denegado(_error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def pagina_no_encontrada(_error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def error_interno(_error):
    db.session.rollback()
    return render_template("errors/500.html"), 500


@app.cli.command("check-db")
def check_db():
    """Comprueba la conexión sin modificar PostgreSQL."""
    try:
        resultado = db.session.execute(
            text(
                "SELECT current_user, current_database(), "
                "pg_encoding_to_char(encoding), pg_get_userbyid(datdba) "
                "FROM pg_database WHERE datname = current_database()"
            )
        ).one()
        click.echo("Conexión con PostgreSQL correcta.")
        click.echo(f"Usuario: {resultado[0]}")
        click.echo(f"Base de datos: {resultado[1]}")
        click.echo(f"Codificación: {resultado[2]}")
        click.echo(f"Propietario: {resultado[3]}")
    except SQLAlchemyError as error:
        db.session.rollback()
        raise click.ClickException(
            "No fue posible conectar con PostgreSQL. Revisa el archivo .env."
        ) from error


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
