"""Punto de entrada de la aplicación New Records."""

from datetime import date
from decimal import Decimal, InvalidOperation
import re

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
from flask_wtf.csrf import CSRFError, CSRFProtect

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
from mailer import enviar_pin, mail, notificar_creacion_pedido
from models import (
    CD,
    Categoria,
    Disco,
    MetodoPago,
    Pedido,
    Usuario,
    VerificacionTarjeta,
    Vinilo,
    db,
)
from payments import (
    crear_verificacion,
    desactivar_metodo_pago,
    establecer_predeterminado,
    obtener_metodos_pago_activos,
    numero_tarjeta_valido,
    verificar_pin,
    vencimiento_tarjeta_valido,
    MARCAS_VALIDAS,
)
from pdf_generator import generar_pdf_pedido
from services import (
    aprobar_pedido,
    generar_codigo_disco,
    obtener_estadisticas_dashboard,
    obtener_pedido_por_numero,
    obtener_pedidos_admin,
    obtener_pedidos_cliente,
    obtener_ranking_categorias,
    obtener_ranking_discos,
    obtener_reporte_ventas_temporal,
    obtener_resumen_metricas_ventas,
    procesar_checkout,
    rechazar_pedido,
)

app = Flask(__name__)
app.config.from_object(Config)
if not app.config.get("SECRET_KEY"):
    raise RuntimeError("Configura SECRET_KEY en el archivo .env antes de iniciar Flask.")
db.init_app(app)
mail.init_app(app)
csrf = CSRFProtect(app)


def es_url_segura(destino):
    """Verifica que la redirección sea interna y no apunte a dominios externos."""
    if not destino:
        return False
    ref_host = urlsplit(request.host_url).netloc
    test_host = urlsplit(destino).netloc
    return not test_host or test_host == ref_host


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
    """Inyecta el usuario actual, sus iniciales, su estado y el contador de ítems del carrito en todas las plantillas."""
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
    
    iniciales = ""
    if usuario and usuario.nombre:
        partes = usuario.nombre.strip().split()
        if len(partes) >= 2:
            iniciales = f"{partes[0][0]}{partes[1][0]}".upper()
        elif len(partes) == 1 and len(partes[0]) >= 2:
            iniciales = partes[0][:2].upper()
        elif len(partes) == 1:
            iniciales = partes[0][0].upper()

    return {
        "usuario_actual": usuario,
        "usuario_iniciales": iniciales or "NR",
        "esta_autenticado": usuario is not None,
        "es_admin": usuario is not None and usuario.rol == "administrador",
        "es_cliente": usuario is not None and usuario.rol == "cliente",
        "categorias_globales": categorias_globales,
        "total_items_carrito": total_items,
    }


@app.route("/")
def inicio():
    """Muestra la portada de New Records solo a usuarios no autenticados o redirige al contenido interno."""
    usuario = obtener_usuario_actual()
    if usuario is not None:
        if usuario.es_administrador():
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("productos"))
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


@app.route("/registro", methods=["GET", "POST"])
def registro():
    """Registra una nueva cuenta pública asignando siempre el rol cliente."""
    es_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.headers.get("Accept", "").startswith("application/json")
        or request.is_json
    )

    if "usuario_id" in session:
        usuario = obtener_usuario_actual()
        if usuario and usuario.es_administrador():
            dest = url_for("admin_dashboard")
        else:
            dest = url_for("productos")
        if es_ajax:
            return jsonify({"ok": True, "redirect": dest})
        return redirect(dest)

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmar_password = request.form.get("confirmar_password", "")

        errores = {}

        if not nombre:
            errores["nombre"] = "El nombre completo es un campo obligatorio."
        elif len(nombre) < 2 or len(nombre) > 100:
            errores["nombre"] = "El nombre debe contener entre 2 y 100 caracteres."

        if not email:
            errores["email"] = "El correo es un campo obligatorio."
        elif Usuario.query.filter_by(email=email).first() is not None:
            errores["email"] = "Ya existe una cuenta registrada con este correo electrónico."
        else:
            try:
                email_normalizado = normalizar_email(email)
                if len(email_normalizado) > 120:
                    errores["email"] = "El correo electrónico no puede superar 120 caracteres."
                elif Usuario.query.filter_by(email=email_normalizado).first() is not None:
                    errores["email"] = "Ya existe una cuenta registrada con este correo electrónico."
                else:
                    email = email_normalizado
            except EmailNotValidError:
                errores["email"] = "El correo debe ser un correo válido. Introduce un correo electrónico válido."

        if not password:
            errores["password"] = "La contraseña es un campo obligatorio."
        elif len(password) < 8:
            errores["password"] = "La contraseña debe tener mínimo 8 caracteres (al menos 8 caracteres)."

        if not confirmar_password:
            errores["confirmar_password"] = "Confirmar contraseña es un campo obligatorio."
        elif password and password != confirmar_password:
            errores["confirmar_password"] = "La contraseña debe coincidir (Las contraseñas no coinciden)."

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
            flash("¡Tu cuenta ha sido creada exitosamente! Ahora puedes iniciar sesión.", "success")
            if es_ajax:
                return jsonify({"ok": True, "redirect": url_for("login")}), 200
            return redirect(url_for("login"))
        except Exception:
            db.session.rollback()
            errores["general"] = "Ocurrió un error al procesar el registro. Inténtalo más tarde."
            if es_ajax:
                return jsonify({"ok": False, "errores": errores}), 500
            return render_template("auth/registro.html", nombre=nombre, email=email, errores=errores)

    return render_template("auth/registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicia la sesión del usuario previa verificación de credenciales."""
    es_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.headers.get("Accept", "").startswith("application/json")
        or request.is_json
    )

    if "usuario_id" in session:
        usuario = obtener_usuario_actual()
        if usuario and usuario.es_administrador():
            dest = url_for("admin_dashboard")
        else:
            dest = url_for("productos")
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
            return render_template("auth/login.html", email=email, next=next_url, errores=errores)

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario is None or not usuario.check_password(password):
            errores["password"] = "Correo electrónico o contraseña incorrectos."
            errores["general"] = "Correo electrónico o contraseña incorrectos."
            if es_ajax:
                return jsonify({"ok": False, "errores": errores}), 400
            return render_template("auth/login.html", email=email, next=next_url, errores=errores)

        if not usuario.activo:
            errores["password"] = "Esta cuenta se encuentra desactivada. Contacta al administrador."
            errores["general"] = "Esta cuenta se encuentra desactivada. Contacta al administrador."
            if es_ajax:
                return jsonify({"ok": False, "errores": errores}), 400
            return render_template("auth/login.html", email=email, next=next_url, errores=errores)

        iniciar_sesion(usuario)
        flash(f"¡Bienvenido de nuevo, {usuario.nombre}!", "success")

        if next_url and es_url_segura(next_url):
            dest = next_url
        elif usuario.es_administrador():
            dest = url_for("admin_dashboard")
        else:
            dest = url_for("productos")

        if es_ajax:
            return jsonify({"ok": True, "redirect": dest}), 200

        return redirect(dest)

    return render_template("auth/login.html", next=next_url)


@app.route("/logout", methods=["POST"])
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

    try:
        pdf_bytes, nombre_archivo, _ = generar_pdf_pedido(
            pedido, tipo="COMPROBANTE_PENDIENTE"
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("No se pudo generar el comprobante. Inténtalo nuevamente.", "error")
        return redirect(url_for("ver_pedido", numero=numero))
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

    try:
        pdf_bytes, nombre_archivo, _ = generar_pdf_pedido(
            pedido, tipo="FACTURA_FINAL"
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("No se pudo generar la factura. Inténtalo nuevamente.", "error")
        return redirect(url_for("ver_pedido", numero=numero))
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
        if not numero_tarjeta_valido(numero_completo):
            errores.append("El número de tarjeta no es válido.")
        try:
            mes_int = int(mes)
            anio_int = int(anio)
            if not (1 <= mes_int <= 12):
                raise ValueError
            if not vencimiento_tarjeta_valido(mes_int, anio_int):
                raise ValueError
        except (ValueError, TypeError):
            errores.append(
                "Ingresa una fecha de vencimiento vigente y válida."
            )

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
                anio_actual=date.today().year,
                mes_actual=date.today().month,
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
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
            return render_template(
                "pago/agregar.html",
                marcas=MARCAS_VALIDAS,
                titular=titular,
                marca=marca,
                mes=mes,
                anio=anio,
                anio_actual=date.today().year,
                mes_actual=date.today().month,
            )
        except Exception:
            db.session.rollback()
            flash("Error al procesar la tarjeta. Inténtalo de nuevo.", "error")
            return render_template(
                "pago/agregar.html",
                marcas=MARCAS_VALIDAS,
                anio_actual=date.today().year,
                mes_actual=date.today().month,
            )

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

    return render_template(
        "pago/agregar.html",
        marcas=MARCAS_VALIDAS,
        anio_actual=date.today().year,
        mes_actual=date.today().month,
    )


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
    """Panel de administración con métricas clave y accesos directos."""
    stats = obtener_estadisticas_dashboard()
    ultimos_pedidos = obtener_pedidos_admin()[:5]
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        ultimos_pedidos=ultimos_pedidos,
    )


@app.route("/admin/reportes")
@rol_requerido("administrador")
def admin_reportes():
    """Módulo de analítica y reportes de ventas con filtros temporales y rankings."""
    periodo = request.args.get("periodo", "diario").strip().lower()
    if periodo not in ("diario", "semanal", "mensual", "anual"):
        periodo = "diario"

    resumen = obtener_resumen_metricas_ventas()
    reporte_temporal = obtener_reporte_ventas_temporal(agrupacion=periodo)
    ranking_discos = obtener_ranking_discos(limite=10)
    ranking_categorias = obtener_ranking_categorias()

    return render_template(
        "admin/reportes.html",
        periodo=periodo,
        resumen=resumen,
        reporte_temporal=reporte_temporal,
        ranking_discos=ranking_discos,
        ranking_categorias=ranking_categorias,
    )


# ── Administración de Discos ─────────────────────────────────────────────────

@app.route("/admin/discos")
@rol_requerido("administrador")
def admin_discos_lista():
    """Lista completa de discos para gestión administrativa."""
    discos = Disco.query.order_by(Disco.activo.desc(), Disco.fecha_creacion.desc()).all()
    return render_template("admin/discos/lista.html", discos=discos)


@app.route("/admin/discos/nuevo", methods=["GET", "POST"])
@rol_requerido("administrador")
def admin_discos_nuevo():
    """Formulario para agregar un nuevo disco al catálogo."""
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()

    if request.method == "POST":
        formato = request.form.get("formato", "").upper().strip()
        album = request.form.get("album", "").strip()
        artista = request.form.get("artista", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        categoria_id = request.form.get("categoria_id")
        precio_base = request.form.get("precio_base", "0")
        stock = request.form.get("stock", "0")
        peso_kg = request.form.get("peso_kg", "0")
        costo_envio = request.form.get("costo_envio_por_kg", "0")
        costo_embalaje = request.form.get("costo_embalaje", "0")
        imagen = request.form.get("imagen", "").strip()

        errores = []
        if formato not in ("CD", "VINILO"):
            errores.append("Selecciona un formato válido (CD o VINILO).")
        if not album:
            errores.append("El nombre del álbum es obligatorio.")
        if not artista:
            errores.append("El nombre del artista es obligatorio.")
        if not descripcion:
            errores.append("La descripción del álbum es obligatoria.")

        try:
            precio_val = Decimal(precio_base)
            stock_val = int(stock)
            peso_val = Decimal(peso_kg)
            envio_val = Decimal(costo_envio)
            embalaje_val = Decimal(costo_embalaje) if formato == "VINILO" else Decimal("0")
            cat_id_val = int(categoria_id)
            categoria_valida = Categoria.query.filter_by(
                id=cat_id_val, activo=True
            ).first()
            if (
                precio_val <= 0
                or stock_val < 0
                or peso_val <= 0
                or envio_val < 0
                or embalaje_val < 0
                or categoria_valida is None
            ):
                raise ValueError
        except (InvalidOperation, ValueError, TypeError):
            errores.append(
                "Verifica la categoría y los valores numéricos: precio y peso deben "
                "ser positivos; stock, envío y embalaje no pueden ser negativos."
            )

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template(
                "admin/discos/formulario.html",
                categorias=categorias,
                disco=None,
                formato=formato,
                album=album,
                artista=artista,
                descripcion=descripcion,
                categoria_id=categoria_id,
                precio_base=precio_base,
                stock=stock,
                peso_kg=peso_kg,
                costo_envio_por_kg=costo_envio,
                costo_embalaje=costo_embalaje,
                imagen=imagen,
            )

        try:
            codigo = generar_codigo_disco(cat_id_val)
            datos_comunes = {
                "categoria_id": cat_id_val,
                "codigo": codigo,
                "album": album,
                "artista": artista,
                "descripcion": descripcion,
                "precio_base": precio_val,
                "stock": stock_val,
                "peso_kg": peso_val,
                "costo_envio_por_kg": envio_val,
                "imagen": imagen or None,
                "activo": True,
            }

            if formato == "VINILO":
                nuevo_disco = Vinilo(
                    **datos_comunes,
                    formato="VINILO",
                    costo_embalaje=embalaje_val,
                )
            else:
                nuevo_disco = CD(
                    **datos_comunes,
                    formato="CD",
                    costo_embalaje=Decimal("0"),
                )

            db.session.add(nuevo_disco)
            db.session.commit()
            flash(
                f"Disco '{album}' creado exitosamente con el código {codigo}.",
                "success",
            )
            return redirect(url_for("admin_discos_lista"))
        except Exception:
            db.session.rollback()
            flash("Error al guardar el disco en la base de datos.", "error")

    return render_template("admin/discos/formulario.html", categorias=categorias, disco=None)


@app.route("/admin/discos/<int:id>/editar", methods=["GET", "POST"])
@rol_requerido("administrador")
def admin_discos_editar(id):
    """Formulario de edición de disco existente."""
    disco = db.get_or_404(Disco, id)
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()

    if request.method == "POST":
        album = request.form.get("album", "").strip()
        artista = request.form.get("artista", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        categoria_id = request.form.get("categoria_id")
        precio_base = request.form.get("precio_base", "0")
        stock = request.form.get("stock", "0")
        peso_kg = request.form.get("peso_kg", "0")
        costo_envio = request.form.get("costo_envio_por_kg", "0")
        costo_embalaje = request.form.get("costo_embalaje", "0")
        imagen = request.form.get("imagen", "").strip()

        errores = []
        if not album:
            errores.append("El nombre del álbum es obligatorio.")
        if not artista:
            errores.append("El nombre del artista es obligatorio.")
        if not descripcion:
            errores.append("La descripción del álbum es obligatoria.")

        try:
            precio_val = Decimal(precio_base)
            stock_val = int(stock)
            peso_val = Decimal(peso_kg)
            envio_val = Decimal(costo_envio)
            embalaje_val = Decimal(costo_embalaje) if disco.formato == "VINILO" else Decimal("0")
            cat_id_val = int(categoria_id)
            categoria_valida = Categoria.query.filter_by(
                id=cat_id_val, activo=True
            ).first()
            if (
                precio_val <= 0
                or stock_val < 0
                or peso_val <= 0
                or envio_val < 0
                or embalaje_val < 0
                or categoria_valida is None
            ):
                raise ValueError
        except (InvalidOperation, ValueError, TypeError):
            errores.append(
                "Verifica la categoría y los valores numéricos: precio y peso deben "
                "ser positivos; stock, envío y embalaje no pueden ser negativos."
            )

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("admin/discos/formulario.html", categorias=categorias, disco=disco)

        try:
            disco.categoria_id = cat_id_val
            disco.album = album
            disco.artista = artista
            disco.descripcion = descripcion
            disco.precio_base = precio_val
            disco.stock = stock_val
            disco.peso_kg = peso_val
            disco.costo_envio_por_kg = envio_val
            if disco.formato == "VINILO":
                disco.costo_embalaje = embalaje_val
            disco.imagen = imagen or None

            db.session.commit()
            flash(f"Disco '{album}' actualizado correctamente.", "success")
            return redirect(url_for("admin_discos_lista"))
        except Exception:
            db.session.rollback()
            flash("Error al actualizar el disco.", "error")

    return render_template("admin/discos/formulario.html", categorias=categorias, disco=disco)


@app.route("/admin/discos/<int:id>/desactivar", methods=["POST"])
@rol_requerido("administrador")
def admin_discos_desactivar(id):
    """Desactiva lógicamente un disco del catálogo público."""
    disco = db.get_or_404(Disco, id)
    try:
        disco.activo = False
        db.session.commit()
        flash(f"Disco '{disco.album}' desactivado del catálogo público.", "info")
    except Exception:
        db.session.rollback()
        flash("No se pudo desactivar el disco.", "error")
    return redirect(url_for("admin_discos_lista"))


@app.route("/admin/discos/<int:id>/reactivar", methods=["POST"])
@rol_requerido("administrador")
def admin_discos_reactivar(id):
    """Reactiva un disco en el catálogo público."""
    disco = db.get_or_404(Disco, id)
    if not disco.categoria.activo:
        flash("Reactiva primero la categoría del disco.", "warning")
        return redirect(url_for("admin_discos_lista"))
    try:
        disco.activo = True
        db.session.commit()
        flash(f"Disco '{disco.album}' reactivado exitosamente.", "success")
    except Exception:
        db.session.rollback()
        flash("No se pudo reactivar el disco.", "error")
    return redirect(url_for("admin_discos_lista"))


# ── Administración de Categorías ─────────────────────────────────────────────

@app.route("/admin/categorias")
@rol_requerido("administrador")
def admin_categorias_lista():
    """Lista de categorías con conteo de discos."""
    categorias = Categoria.query.order_by(Categoria.activo.desc(), Categoria.nombre).all()
    return render_template("admin/categorias/lista.html", categorias=categorias)


@app.route("/admin/categorias/nueva", methods=["GET", "POST"])
@rol_requerido("administrador")
def admin_categorias_nueva():
    """Formulario para crear una nueva categoría musical."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        slug = request.form.get("slug", "").strip().lower()
        prefijo_codigo = request.form.get("prefijo_codigo", "").strip().upper()
        descripcion = request.form.get("descripcion", "").strip()
        imagen = request.form.get("imagen", "").strip()

        if not slug and nombre:
            slug = re.sub(r"[^\w\s-]", "", nombre.lower()).strip()
            slug = re.sub(r"[-\s]+", "-", slug)

        errores = []
        if not nombre or len(nombre) < 2:
            errores.append("El nombre de la categoría es obligatorio (mínimo 2 caracteres).")
        if not slug:
            errores.append("El slug de la categoría es obligatorio.")
        elif Categoria.query.filter_by(slug=slug).first() is not None:
            errores.append(f"Ya existe una categoría con el slug '{slug}'.")
        if not re.fullmatch(r"[A-Z0-9]{3,5}", prefijo_codigo):
            errores.append(
                "El prefijo debe contener entre 3 y 5 letras mayúsculas o números."
            )
        elif (
            Categoria.query.filter_by(prefijo_codigo=prefijo_codigo).first()
            is not None
        ):
            errores.append(f"El prefijo '{prefijo_codigo}' ya está en uso.")

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template(
                "admin/categorias/formulario.html",
                categoria=None,
                nombre=nombre,
                slug=slug,
                prefijo_codigo=prefijo_codigo,
                descripcion=descripcion,
                imagen=imagen,
            )

        try:
            nueva_cat = Categoria(
                nombre=nombre,
                slug=slug,
                prefijo_codigo=prefijo_codigo,
                descripcion=descripcion or None,
                imagen=imagen or None,
                activo=True,
            )
            db.session.add(nueva_cat)
            db.session.commit()
            flash(f"Categoría '{nombre}' creada exitosamente.", "success")
            return redirect(url_for("admin_categorias_lista"))
        except Exception:
            db.session.rollback()
            flash("Error al crear la categoría.", "error")

    return render_template("admin/categorias/formulario.html", categoria=None)


@app.route("/admin/categorias/<int:id>/editar", methods=["GET", "POST"])
@rol_requerido("administrador")
def admin_categorias_editar(id):
    """Formulario de edición de categoría."""
    categoria = db.get_or_404(Categoria, id)

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        slug = request.form.get("slug", "").strip().lower()
        prefijo_codigo = request.form.get(
            "prefijo_codigo", categoria.prefijo_codigo
        ).strip().upper()
        descripcion = request.form.get("descripcion", "").strip()
        imagen = request.form.get("imagen", "").strip()

        errores = []
        if not nombre or len(nombre) < 2:
            errores.append("El nombre de la categoría es obligatorio.")
        if not slug:
            errores.append("El slug de la categoría es obligatorio.")
        else:
            cat_existente = Categoria.query.filter_by(slug=slug).first()
            if cat_existente and cat_existente.id != categoria.id:
                errores.append(f"El slug '{slug}' ya está en uso por otra categoría.")
        if not re.fullmatch(r"[A-Z0-9]{3,5}", prefijo_codigo):
            errores.append(
                "El prefijo debe contener entre 3 y 5 letras mayúsculas o números."
            )
        else:
            prefijo_existente = Categoria.query.filter_by(
                prefijo_codigo=prefijo_codigo
            ).first()
            if prefijo_existente and prefijo_existente.id != categoria.id:
                errores.append(f"El prefijo '{prefijo_codigo}' ya está en uso.")
            elif (
                prefijo_codigo != categoria.prefijo_codigo
                and Disco.query.filter_by(categoria_id=categoria.id).first()
                is not None
            ):
                errores.append(
                    "El prefijo no puede cambiar porque la categoría ya tiene discos."
                )

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template(
                "admin/categorias/formulario.html",
                categoria=categoria,
                prefijo_codigo=prefijo_codigo,
            )

        try:
            categoria.nombre = nombre
            categoria.slug = slug
            categoria.prefijo_codigo = prefijo_codigo
            categoria.descripcion = descripcion or None
            categoria.imagen = imagen or None
            db.session.commit()
            flash(f"Categoría '{nombre}' actualizada correctamente.", "success")
            return redirect(url_for("admin_categorias_lista"))
        except Exception:
            db.session.rollback()
            flash("Error al actualizar la categoría.", "error")

    return render_template("admin/categorias/formulario.html", categoria=categoria)


@app.route("/admin/categorias/<int:id>/desactivar", methods=["POST"])
@rol_requerido("administrador")
def admin_categorias_desactivar(id):
    """Desactiva una categoría y exige confirmar la cascada sobre sus discos."""
    categoria = db.get_or_404(Categoria, id)
    discos_activos = Disco.query.filter_by(categoria_id=id, activo=True).count()
    confirmacion = request.form.get("confirmar_con_discos") == "si"

    if discos_activos and not confirmacion:
        flash(
            f"La categoría tiene {discos_activos} disco(s) activo(s). "
            "Confirma explícitamente la desactivación conjunta.",
            "warning",
        )
        return redirect(url_for("admin_categorias_lista"))

    try:
        if discos_activos:
            Disco.query.filter_by(categoria_id=id, activo=True).update(
                {"activo": False}, synchronize_session=False
            )
        categoria.activo = False
        db.session.commit()
        flash(
            f"Categoría '{categoria.nombre}' desactivada junto con "
            f"{discos_activos} disco(s) activo(s).",
            "info",
        )
    except Exception:
        db.session.rollback()
        flash("No se pudo desactivar la categoría.", "error")
    return redirect(url_for("admin_categorias_lista"))


@app.route("/admin/categorias/<int:id>/reactivar", methods=["POST"])
@rol_requerido("administrador")
def admin_categorias_reactivar(id):
    """Reactiva una categoría."""
    categoria = db.get_or_404(Categoria, id)
    try:
        categoria.activo = True
        db.session.commit()
        flash(
            f"Categoría '{categoria.nombre}' reactivada. "
            "Sus discos deben reactivarse individualmente.",
            "success",
        )
    except Exception:
        db.session.rollback()
        flash("No se pudo reactivar la categoría.", "error")
    return redirect(url_for("admin_categorias_lista"))


# ── Administración de Pedidos ────────────────────────────────────────────────

@app.route("/admin/pedidos")
@rol_requerido("administrador")
def admin_pedidos_lista():
    """Bandeja administrativa de pedidos con filtros por estado."""
    estado = request.args.get("estado", "").strip().upper()
    pedidos = obtener_pedidos_admin(estado=estado if estado in ("PENDIENTE", "APROBADO", "RECHAZADO") else None)
    return render_template("admin/pedidos/lista.html", pedidos=pedidos, estado_filtro=estado)


@app.route("/admin/pedidos/<numero>")
@rol_requerido("administrador")
def admin_pedido_detalle(numero):
    """Auditoría y detalle administrativo de un pedido con comprobación de stock."""
    pedido = Pedido.query.filter_by(numero=numero).first_or_404()
    return render_template("admin/pedidos/detalle.html", pedido=pedido)


@app.route("/admin/pedidos/<numero>/aprobar", methods=["POST"])
@rol_requerido("administrador")
def admin_pedido_aprobar(numero):
    """Ejecuta la aprobación atómica de un pedido descontando existencias físicas."""
    exito, mensaje = aprobar_pedido(numero, session["usuario_id"])
    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "error")
    return redirect(url_for("admin_pedido_detalle", numero=numero))


@app.route("/admin/pedidos/<numero>/rechazar", methods=["POST"])
@rol_requerido("administrador")
def admin_pedido_rechazar(numero):
    """Ejecuta el rechazo de un pedido con registro obligatorio de motivo."""
    motivo = request.form.get("motivo", "").strip()
    exito, mensaje = rechazar_pedido(numero, session["usuario_id"], motivo)
    if exito:
        flash(mensaje, "info")
    else:
        flash(mensaje, "error")
    return redirect(url_for("admin_pedido_detalle", numero=numero))


@app.after_request
def agregar_cabeceras_seguridad(response):
    """Añade seguridad y convierte redirecciones HTMX en navegación parcial."""
    if (
        request.headers.get("HX-Request") == "true"
        and response.status_code in {301, 302, 303, 307, 308}
        and response.headers.get("Location")
    ):
        destino = response.headers.pop("Location")
        response.status_code = 204
        response.headers["HX-Location"] = destino

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.errorhandler(403)
def acceso_denegado(_error):
    return render_template("errors/403.html"), 403


@app.errorhandler(CSRFError)
def csrf_invalido(_error):
    """Rechaza formularios sin token sin exponer detalles internos."""
    flash("La solicitud expiró o no es válida. Inténtalo nuevamente.", "error")
    destino = request.referrer if es_url_segura(request.referrer) else url_for("inicio")
    return redirect(destino)


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


@app.cli.command("crear-backup")
@click.option(
    "--formato",
    type=click.Choice(["plain", "custom"], case_sensitive=False),
    default="plain",
    help="Formato de salida: 'plain' (.sql) o 'custom' (.dump).",
)
def crear_backup(formato):
    """Genera un respaldo de la base de datos PostgreSQL en la carpeta backups/."""
    from backup_manager import ejecutar_backup_pg_dump

    click.echo(f"Iniciando respaldo en formato {formato.upper()}...")
    exito, resultado, tamano = ejecutar_backup_pg_dump(formato=formato)
    if exito:
        click.echo("¡Respaldo creado exitosamente!")
        click.echo(f"Archivo: {resultado}")
        click.echo(f"Tamaño: {round(tamano / 1024, 2)} KB")
    else:
        click.echo(f"Aviso: {resultado}")
        click.echo(
            "Consulta docs/SEGURIDAD_Y_RESPALDOS.md para instrucciones de respaldo manual."
        )


@app.cli.command("verificar-restauracion")
def verificar_restauracion():
    """Restaura un dump en una base temporal y valida su contenido."""
    from backup_manager import verificar_restauracion_completa

    click.echo("Creando y restaurando una copia temporal de verificación...")
    exito, mensaje, resumen = verificar_restauracion_completa()
    if not exito:
        raise click.ClickException(mensaje)
    click.echo(mensaje)
    click.echo(
        f"Tablas: {resumen['tablas']} | Categorías: {resumen['categorias']} | "
        f"Discos: {resumen['discos']}"
    )


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])

