"""Punto de entrada de la aplicación New Records."""

import click
from email_validator import EmailNotValidError, validate_email
from flask import (
    Flask,
    Response,
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
from mailer import enviar_pin, mail, notificar_creacion_pedido, smtp_configurado
from models import Categoria, Disco, Factura, MetodoPago, VerificacionTarjeta, Usuario, db
from payments import (
    crear_verificacion,
    desactivar_metodo_pago,
    establecer_predeterminado,
    obtener_metodos_pago_activos,
    verificar_pin,
    MARCAS_VALIDAS,
)
from pdf_generator import generar_pdf_pedido
from services import (
    obtener_pedido_por_numero,
    obtener_pedidos_cliente,
    procesar_checkout,
)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail.init_app(app)


def es_url_segura(destino):
    """Verifica que la redirección sea interna y no apunte a dominios externos."""
    if not destino:
        return False
    ref_host = urlsplit(request.host_url).netloc
    test_host = urlsplit(destino).netloc
    return not test_host or test_host == ref_host


def normalizar_email(email):
    """Valida la estructura del correo y retorna una versión normalizada."""
    resultado = validate_email(email, check_deliverability=False)
    return resultado.normalized.strip().lower()


@app.context_processor
def inyectar_contexto_usuario():
    """Inyecta el usuario actual, su estado y el contador de ítems del carrito en todas las plantillas."""
    usuario = obtener_usuario_actual()
    carrito = obtener_carrito_sesion()
    total_items = sum(
        cantidad
        for cantidad in carrito.values()
        if isinstance(cantidad, int) and not isinstance(cantidad, bool) and cantidad > 0
    )
    categorias_globales = (
        Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    )
    return {
        "usuario_actual": usuario,
        "esta_autenticado": usuario is not None,
        "es_admin": usuario is not None and usuario.rol == "administrador",
        "es_cliente": usuario is not None and usuario.rol == "cliente",
        "categorias_globales": categorias_globales,
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

        if len(nombre) < 2 or len(nombre) > 100:
            flash("El nombre debe contener entre 2 y 100 caracteres.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

        if Usuario.query.filter_by(email=email).first() is not None:
            flash("Ya existe una cuenta registrada con este correo electrónico.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

        try:
            email = normalizar_email(email)
        except EmailNotValidError:
            flash("Introduce un correo electrónico válido.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

        if len(email) > 120:
            flash("El correo electrónico no puede superar 120 caracteres.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

        if Usuario.query.filter_by(email=email).first() is not None:
            flash("Ya existe una cuenta registrada con este correo electrónico.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "error")
            return render_template("auth/registro.html", nombre=nombre, email=email)

        if password != confirmar_password:
            flash("Las contraseñas no coinciden. Inténtalo de nuevo.", "error")
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

        if len(nombre) < 2 or len(nombre) > 100:
            flash("El nombre debe contener entre 2 y 100 caracteres.", "error")
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
            return redirect(url_for("perfil"))
        except Exception:
            db.session.rollback()
            flash("Error al actualizar el perfil. Inténtalo de nuevo.", "error")

    return render_template("auth/perfil.html", usuario=usuario)


@app.route("/carrito")
@rol_requerido("cliente")
def ver_carrito():
    """Muestra los productos del carrito con subtotales polimórficos y total general."""
    detalle_carrito = obtener_detalle_carrito()
    return render_template("carrito.html", carrito=detalle_carrito)


@app.route("/carrito/agregar/<int:disco_id>", methods=["POST"])
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
    return redirect(url_for("ver_carrito"))


@app.route("/carrito/actualizar/<int:disco_id>", methods=["POST"])
@rol_requerido("cliente")
def actualizar_carrito(disco_id):
    """Actualiza la cantidad solicitada para un disco del carrito."""
    try:
        cantidad = int(request.form.get("cantidad", 1))
    except (ValueError, TypeError):
        cantidad = 1

    actualizar_cantidad(disco_id, cantidad)
    return redirect(url_for("ver_carrito"))


@app.route("/carrito/eliminar/<int:disco_id>", methods=["POST"])
@rol_requerido("cliente")
def eliminar_del_carrito(disco_id):
    """Remueve un disco del carrito."""
    eliminar_disco(disco_id)
    return redirect(url_for("ver_carrito"))


@app.route("/carrito/vaciar", methods=["POST"])
@rol_requerido("cliente")
def vaciar_carrito_ruta():
    """Vacía completamente el carrito."""
    vaciar_carrito()
    flash("Se vació el carrito correctamente.", "info")
    return redirect(url_for("ver_carrito"))


@app.route("/checkout/resumen")
@rol_requerido("cliente")
def checkout_resumen():
    """Muestra el resumen previo del pedido antes del pago y confirmación."""
    detalle_carrito = obtener_detalle_carrito()

    if not detalle_carrito["elementos"]:
        flash("Tu carrito está vacío. Agrega productos antes de ir al checkout.", "warning")
        return redirect(url_for("ver_carrito"))

    usuario = obtener_usuario_actual()
    metodos_pago = obtener_metodos_pago_activos(usuario.id)
    return render_template(
        "checkout_resumen.html",
        carrito=detalle_carrito,
        usuario=usuario,
        metodos_pago=metodos_pago,
    )


@app.route("/checkout/confirmar", methods=["POST"])
@rol_requerido("cliente")
def confirmar_checkout():
    """Procesa el checkout y crea el pedido persistente con cobro simulado."""
    metodo_pago_id = request.form.get("metodo_pago_id")
    if not metodo_pago_id:
        flash("Debes seleccionar un método de pago verificado para continuar.", "error")
        return redirect(url_for("checkout_resumen"))

    try:
        metodo_id_int = int(metodo_pago_id)
    except (ValueError, TypeError):
        flash("Método de pago inválido.", "error")
        return redirect(url_for("checkout_resumen"))

    exito, resultado = procesar_checkout(session["usuario_id"], metodo_id_int)
    if exito:
        # Enviar notificación por correo (si SMTP está configurado)
        notificar_creacion_pedido(resultado)
        flash(f"¡Tu pedido {resultado.numero} ha sido creado con éxito! Se encuentra pendiente de revisión.", "success")
        return redirect(url_for("ver_pedido", numero=resultado.numero))
    else:
        flash(resultado, "error")
        return redirect(url_for("checkout_resumen"))


@app.route("/pedidos")
@rol_requerido("cliente")
def lista_pedidos():
    """Muestra el historial de pedidos realizados por el cliente autenticado."""
    pedidos = obtener_pedidos_cliente(session["usuario_id"])
    return render_template("pedidos/lista.html", pedidos=pedidos)


@app.route("/pedidos/<numero>")
@login_requerido
def ver_pedido(numero):
    """Muestra el detalle completo de un pedido específico."""
    usuario = obtener_usuario_actual()
    pedido = obtener_pedido_por_numero(numero, usuario)
    if not pedido:
        return render_template("errors/404.html"), 404

    return render_template("pedidos/detalle.html", pedido=pedido)


@app.route("/pedidos/<numero>/comprobante")
@login_requerido
def descargar_comprobante(numero):
    """Genera y transmite el comprobante de pedido en formato PDF."""
    usuario = obtener_usuario_actual()
    pedido = obtener_pedido_por_numero(numero, usuario)
    if not pedido:
        return render_template("errors/404.html"), 404

    pdf_bytes, nombre_archivo, _ = generar_pdf_pedido(pedido, tipo="COMPROBANTE_PENDIENTE")
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={nombre_archivo}"},
    )


@app.route("/pedidos/<numero>/factura")
@login_requerido
def descargar_factura(numero):
    """Genera y transmite la factura final de venta en formato PDF tras aprobación."""
    usuario = obtener_usuario_actual()
    pedido = obtener_pedido_por_numero(numero, usuario)
    if not pedido:
        return render_template("errors/404.html"), 404

    if pedido.estado != "APROBADO":
        flash("La Factura Oficial de venta solo está disponible una vez que el pedido haya sido APROBADO.", "warning")
        return redirect(url_for("ver_pedido", numero=numero))

    pdf_bytes, nombre_archivo, _ = generar_pdf_pedido(pedido, tipo="FACTURA_FINAL")
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={nombre_archivo}"},
    )


@app.route("/pago/metodos")
@rol_requerido("cliente")
def pago_metodos():
    """Muestra los métodos de pago verificados del cliente."""
    metodos = obtener_metodos_pago_activos(session["usuario_id"])
    return render_template("pago/metodos.html", metodos=metodos)


@app.route("/pago/agregar", methods=["GET", "POST"])
@rol_requerido("cliente")
def pago_agregar():
    """Formulario de registro de nueva tarjeta; genera y envía el PIN de verificación."""
    if request.method == "POST":
        titular = request.form.get("titular", "").strip()
        marca = request.form.get("marca", "").upper().strip()
        numero_completo = request.form.get("numero", "").replace(" ", "").replace("-", "")
        mes = request.form.get("mes_vencimiento", "").strip()
        anio = request.form.get("anio_vencimiento", "").strip()

        errores = []
        if not titular or len(titular) < 3:
            errores.append("El nombre del titular es obligatorio (mínimo 3 caracteres).")
        if marca not in MARCAS_VALIDAS:
            errores.append("Selecciona una marca de tarjeta válida.")
        if not numero_completo.isdigit() or len(numero_completo) < 13 or len(numero_completo) > 19:
            errores.append("El número de tarjeta debe tener entre 13 y 19 dígitos.")
        try:
            mes_int = int(mes)
            anio_int = int(anio)
            if not (1 <= mes_int <= 12):
                raise ValueError
            if anio_int < 2026:
                raise ValueError
        except (ValueError, TypeError):
            errores.append("Ingresa un mes (1-12) y año de vencimiento válidos.")

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template(
                "pago/agregar.html",
                marcas=MARCAS_VALIDAS,
                titular=titular,
                marca=marca,
                mes=mes,
                anio=anio,
            )

        ultimos4 = numero_completo[-4:]
        datos = {
            "marca": marca,
            "ultimos4": ultimos4,
            "titular": titular,
            "mes_vencimiento": mes_int,
            "anio_vencimiento": anio_int,
        }

        try:
            verificacion, pin = crear_verificacion(session["usuario_id"], datos)
        except Exception:
            db.session.rollback()
            flash("Error al procesar la tarjeta. Inténtalo de nuevo.", "error")
            return render_template("pago/agregar.html", marcas=MARCAS_VALIDAS)

        usuario = obtener_usuario_actual()
        enviado = enviar_pin(usuario.email, usuario.nombre, pin)

        if enviado:
            flash(
                f"Se envió un código de 6 dígitos a {usuario.email}. Ingresa el código para confirmar tu tarjeta.",
                "info",
            )
        else:
            # Modo desarrollo: mostrar PIN en flash si SMTP no está configurado
            flash(
                f"[MODO DESARROLLO] El SMTP no está configurado. Tu PIN de verificación es: {pin}",
                "warning",
            )

        return redirect(url_for("pago_verificar", token=verificacion.token_verificacion))

    return render_template("pago/agregar.html", marcas=MARCAS_VALIDAS)


@app.route("/pago/verificar/<token>", methods=["GET", "POST"])
@rol_requerido("cliente")
def pago_verificar(token):
    """Formulario de ingreso del PIN para confirmar el registro de la tarjeta."""
    verificacion = VerificacionTarjeta.query.filter_by(
        token_verificacion=token, usuario_id=session["usuario_id"]
    ).first_or_404()

    if verificacion.verificada:
        flash("Esta verificación ya fue completada.", "info")
        return redirect(url_for("pago_metodos"))

    if request.method == "POST":
        pin_ingresado = request.form.get("pin", "").strip()
        exito, resultado = verificar_pin(token, pin_ingresado)

        if exito:
            flash("¡Tarjeta verificada y agregada correctamente a tus métodos de pago!", "success")
            return redirect(url_for("pago_metodos"))
        else:
            flash(resultado, "error")

    intentos_restantes = max(0, 3 - verificacion.intentos)
    return render_template(
        "pago/verificar_pin.html",
        token=token,
        verificacion=verificacion,
        intentos_restantes=intentos_restantes,
    )


@app.route("/pago/predeterminado/<int:metodo_id>", methods=["POST"])
@rol_requerido("cliente")
def pago_predeterminado(metodo_id):
    """Establece un método de pago como predeterminado del cliente."""
    if establecer_predeterminado(metodo_id, session["usuario_id"]):
        flash("Método de pago predeterminado actualizado.", "success")
    else:
        flash("No se encontró el método de pago indicado.", "error")
    return redirect(url_for("pago_metodos"))


@app.route("/pago/eliminar/<int:metodo_id>", methods=["POST"])
@rol_requerido("cliente")
def pago_eliminar(metodo_id):
    """Desactiva (eliminación lógica) un método de pago del cliente."""
    if desactivar_metodo_pago(metodo_id, session["usuario_id"]):
        flash("Método de pago eliminado correctamente.", "info")
    else:
        flash("No se encontró el método de pago indicado.", "error")
    return redirect(url_for("pago_metodos"))


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
