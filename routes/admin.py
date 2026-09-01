"""Rutas administrativas de panel, catálogo, pedidos y reportes."""

import math
from decimal import Decimal

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

from auth import rol_requerido
from models import CD, Categoria, Disco, Pedido, Vinilo, db
from services import (
    aprobar_pedido,
    generar_codigo_disco,
    obtener_estadisticas_dashboard,
    obtener_pedidos_admin,
    obtener_ranking_categorias,
    obtener_ranking_discos,
    obtener_reporte_ventas_temporal,
    obtener_resumen_metricas_ventas,
    rechazar_pedido,
)
from uploads import eliminar_imagen_gestionada, guardar_imagen_subida
from validators import (
    convertir_valores_disco,
    prefijo_categoria_valido,
    slugificar,
    validar_nombre_categoria,
    validar_textos_disco,
)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/dashboard")
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


@admin_bp.route("/admin/reportes")
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


@admin_bp.route("/admin/discos")
@rol_requerido("administrador")
def admin_discos_lista():
    """Lista de discos con filtros por género/formato y paginación (5 por página)."""
    pagina = request.args.get("pagina", 1, type=int)
    if pagina < 1:
        pagina = 1
    por_pagina = 5

    categoria_id = request.args.get("categoria_id", "").strip()
    formato = request.args.get("formato", "").strip().upper()

    query = Disco.query
    if categoria_id and categoria_id.isdigit():
        query = query.filter_by(categoria_id=int(categoria_id))
    if formato in ("CD", "VINILO"):
        query = query.filter_by(formato=formato)

    query = query.order_by(Disco.activo.desc(), Disco.fecha_creacion.desc())
    total = query.count()
    total_paginas = max(1, math.ceil(total / por_pagina))
    if pagina > total_paginas:
        pagina = total_paginas

    discos = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()

    if (
        request.args.get("ajax") == "1"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        html_cards = render_template("admin/discos/_cards_movil.html", discos=discos)
        return jsonify(
            {
                "html": html_cards,
                "pagina": pagina,
                "total_paginas": total_paginas,
                "total": total,
                "tiene_mas": pagina < total_paginas,
            }
        )

    return render_template(
        "admin/discos/lista.html",
        discos=discos,
        categorias=categorias,
        categoria_filtro=categoria_id,
        formato_filtro=formato,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total,
        por_pagina=por_pagina,
    )


@admin_bp.route("/admin/discos/nuevo", methods=["GET", "POST"])
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

        errores = validar_textos_disco(
            formato=formato,
            album=album,
            artista=artista,
            descripcion=descripcion,
        )
        valores = convertir_valores_disco(
            precio_base=precio_base,
            stock=stock,
            peso_kg=peso_kg,
            costo_envio_por_kg=costo_envio,
            costo_embalaje=costo_embalaje if formato == "VINILO" else "0",
            categoria_id=categoria_id,
        )
        categoria_valida = (
            Categoria.query.filter_by(id=valores.categoria_id, activo=True).first()
            if valores
            else None
        )
        if valores is None or categoria_valida is None:
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
                imagen=None,
            )

        imagen_nueva = None
        try:
            imagen_nueva = guardar_imagen_subida(
                request.files.get("imagen_archivo"), "productos"
            )
            precio_val = valores.precio_base
            stock_val = valores.stock
            peso_val = valores.peso_kg
            envio_val = valores.costo_envio_por_kg
            embalaje_val = valores.costo_embalaje
            cat_id_val = valores.categoria_id
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
                "imagen": imagen_nueva,
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
            return redirect(url_for("admin.admin_discos_lista"))
        except ValueError as error:
            db.session.rollback()
            eliminar_imagen_gestionada(imagen_nueva)
            flash(str(error), "error")
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
                imagen=None,
            )
        except Exception:
            db.session.rollback()
            eliminar_imagen_gestionada(imagen_nueva)
            flash("No se pudo guardar el disco. Inténtalo nuevamente.", "error")

    return render_template(
        "admin/discos/formulario.html", categorias=categorias, disco=None
    )


@admin_bp.route("/admin/discos/<int:id>/editar", methods=["GET", "POST"])
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
        conservar_imagen = (
            request.form.get("conservar_imagen", "1" if disco.imagen else "0") == "1"
        )

        errores = validar_textos_disco(
            formato=disco.formato,
            album=album,
            artista=artista,
            descripcion=descripcion,
        )
        valores = convertir_valores_disco(
            precio_base=precio_base,
            stock=stock,
            peso_kg=peso_kg,
            costo_envio_por_kg=costo_envio,
            costo_embalaje=costo_embalaje if disco.formato == "VINILO" else "0",
            categoria_id=categoria_id,
        )
        categoria_valida = (
            Categoria.query.filter_by(id=valores.categoria_id, activo=True).first()
            if valores
            else None
        )
        if valores is None or categoria_valida is None:
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
                disco=disco,
                imagen=disco.imagen if conservar_imagen else None,
            )

        imagen_anterior = disco.imagen
        imagen_nueva = None
        try:
            imagen_nueva = guardar_imagen_subida(
                request.files.get("imagen_archivo"), "productos"
            )
            precio_val = valores.precio_base
            stock_val = valores.stock
            peso_val = valores.peso_kg
            envio_val = valores.costo_envio_por_kg
            embalaje_val = valores.costo_embalaje
            cat_id_val = valores.categoria_id
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
            disco.imagen = imagen_nueva or (
                imagen_anterior if conservar_imagen else None
            )

            db.session.commit()
            if imagen_anterior != disco.imagen:
                eliminar_imagen_gestionada(imagen_anterior)
            flash(f"Disco '{album}' actualizado correctamente.", "success")
            return redirect(url_for("admin.admin_discos_lista"))
        except ValueError as error:
            db.session.rollback()
            eliminar_imagen_gestionada(imagen_nueva)
            flash(str(error), "error")
            return render_template(
                "admin/discos/formulario.html",
                categorias=categorias,
                disco=disco,
                imagen=imagen_anterior if conservar_imagen else None,
            )
        except Exception:
            db.session.rollback()
            eliminar_imagen_gestionada(imagen_nueva)
            flash("Error al actualizar el disco.", "error")

    return render_template(
        "admin/discos/formulario.html", categorias=categorias, disco=disco
    )


@admin_bp.route("/admin/discos/<int:id>/desactivar", methods=["POST"])
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
    return redirect(url_for("admin.admin_discos_lista"))


@admin_bp.route("/admin/discos/<int:id>/reactivar", methods=["POST"])
@rol_requerido("administrador")
def admin_discos_reactivar(id):
    """Reactiva un disco en el catálogo público."""
    disco = db.get_or_404(Disco, id)
    if not disco.categoria.activo:
        flash("Reactiva primero la categoría del disco.", "warning")
        return redirect(url_for("admin.admin_discos_lista"))
    try:
        disco.activo = True
        db.session.commit()
        flash(f"Disco '{disco.album}' reactivado exitosamente.", "success")
    except Exception:
        db.session.rollback()
        flash("No se pudo reactivar el disco.", "error")
    return redirect(url_for("admin.admin_discos_lista"))


# ── Administración de Categorías ─────────────────────────────────────────────


@admin_bp.route("/admin/categorias")
@rol_requerido("administrador")
def admin_categorias_lista():
    """Lista de categorías con conteo de discos y paginación (5 por página)."""
    pagina = request.args.get("pagina", 1, type=int)
    if pagina < 1:
        pagina = 1
    por_pagina = 5

    query = Categoria.query.order_by(Categoria.activo.desc(), Categoria.nombre)
    total = query.count()
    total_paginas = max(1, math.ceil(total / por_pagina))
    if pagina > total_paginas:
        pagina = total_paginas

    categorias = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

    return render_template(
        "admin/categorias/lista.html",
        categorias=categorias,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total,
        por_pagina=por_pagina,
    )


@admin_bp.route("/admin/categorias/nueva", methods=["GET", "POST"])
@rol_requerido("administrador")
def admin_categorias_nueva():
    """Formulario para crear una nueva categoría musical."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        slug = request.form.get("slug", "").strip().lower()
        prefijo_codigo = request.form.get("prefijo_codigo", "").strip().upper()
        descripcion = request.form.get("descripcion", "").strip()

        if not slug and nombre:
            slug = slugificar(nombre)

        errores = []
        error_nombre = validar_nombre_categoria(nombre)
        if error_nombre:
            errores.append(error_nombre)
        if not slug:
            errores.append("No se pudo generar el identificador de la categoría.")
        elif Categoria.query.filter_by(slug=slug).first() is not None:
            errores.append("Ya existe una categoría con un nombre equivalente.")
        if not prefijo_categoria_valido(prefijo_codigo):
            errores.append(
                "El prefijo debe contener entre 3 y 5 letras mayúsculas o números."
            )
        elif (
            Categoria.query.filter_by(prefijo_codigo=prefijo_codigo).first() is not None
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
                imagen=None,
            )

        imagen_nueva = None
        try:
            imagen_nueva = guardar_imagen_subida(
                request.files.get("imagen_archivo"), "categorias"
            )
            nueva_cat = Categoria(
                nombre=nombre,
                slug=slug,
                prefijo_codigo=prefijo_codigo,
                descripcion=descripcion or None,
                imagen=imagen_nueva,
                activo=True,
            )
            db.session.add(nueva_cat)
            db.session.commit()
            flash(f"Categoría '{nombre}' creada exitosamente.", "success")
            return redirect(url_for("admin.admin_categorias_lista"))
        except ValueError as error:
            db.session.rollback()
            eliminar_imagen_gestionada(imagen_nueva)
            flash(str(error), "error")
            return render_template(
                "admin/categorias/formulario.html",
                categoria=None,
                nombre=nombre,
                slug=slug,
                prefijo_codigo=prefijo_codigo,
                descripcion=descripcion,
                imagen=None,
            )
        except Exception:
            db.session.rollback()
            eliminar_imagen_gestionada(imagen_nueva)
            flash("Error al crear la categoría.", "error")

    return render_template("admin/categorias/formulario.html", categoria=None)


@admin_bp.route("/admin/categorias/<int:id>/editar", methods=["GET", "POST"])
@rol_requerido("administrador")
def admin_categorias_editar(id):
    """Formulario de edición de categoría."""
    categoria = db.get_or_404(Categoria, id)

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        slug = request.form.get("slug", categoria.slug).strip().lower()
        prefijo_codigo = (
            request.form.get("prefijo_codigo", categoria.prefijo_codigo).strip().upper()
        )
        descripcion = request.form.get("descripcion", "").strip()
        conservar_imagen = (
            request.form.get("conservar_imagen", "1" if categoria.imagen else "0")
            == "1"
        )

        errores = []
        error_nombre = validar_nombre_categoria(nombre)
        if error_nombre:
            errores.append(error_nombre)
        if not slug:
            errores.append("No se pudo conservar el identificador de la categoría.")
        else:
            cat_existente = Categoria.query.filter_by(slug=slug).first()
            if cat_existente and cat_existente.id != categoria.id:
                errores.append(
                    "Ya existe una categoría con un identificador equivalente."
                )
        if not prefijo_categoria_valido(prefijo_codigo):
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
                and Disco.query.filter_by(categoria_id=categoria.id).first() is not None
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
                imagen=categoria.imagen if conservar_imagen else None,
            )

        imagen_anterior = categoria.imagen
        imagen_nueva = None
        try:
            imagen_nueva = guardar_imagen_subida(
                request.files.get("imagen_archivo"), "categorias"
            )
            categoria.nombre = nombre
            categoria.slug = slug
            categoria.prefijo_codigo = prefijo_codigo
            categoria.descripcion = descripcion or None
            categoria.imagen = imagen_nueva or (
                imagen_anterior if conservar_imagen else None
            )
            db.session.commit()
            if imagen_anterior != categoria.imagen:
                eliminar_imagen_gestionada(imagen_anterior)
            flash(f"Categoría '{nombre}' actualizada correctamente.", "success")
            return redirect(url_for("admin.admin_categorias_lista"))
        except ValueError as error:
            db.session.rollback()
            eliminar_imagen_gestionada(imagen_nueva)
            flash(str(error), "error")
            return render_template(
                "admin/categorias/formulario.html",
                categoria=categoria,
                prefijo_codigo=prefijo_codigo,
                imagen=imagen_anterior if conservar_imagen else None,
            )
        except Exception:
            db.session.rollback()
            eliminar_imagen_gestionada(imagen_nueva)
            flash("Error al actualizar la categoría.", "error")

    return render_template("admin/categorias/formulario.html", categoria=categoria)


@admin_bp.route("/admin/categorias/<int:id>/desactivar", methods=["POST"])
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
        return redirect(url_for("admin.admin_categorias_lista"))

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
    return redirect(url_for("admin.admin_categorias_lista"))


@admin_bp.route("/admin/categorias/<int:id>/reactivar", methods=["POST"])
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
    return redirect(url_for("admin.admin_categorias_lista"))


# ── Administración de Pedidos ────────────────────────────────────────────────


@admin_bp.route("/admin/pedidos")
@rol_requerido("administrador")
def admin_pedidos_lista():
    """Bandeja administrativa de pedidos con filtros por estado y paginación (5 por página)."""
    pagina = request.args.get("pagina", 1, type=int)
    if pagina < 1:
        pagina = 1
    por_pagina = 5

    estado = request.args.get("estado", "").strip().upper()
    pedidos_todos = obtener_pedidos_admin(
        estado=estado if estado in ("PENDIENTE", "APROBADO", "RECHAZADO") else None
    )
    total = len(pedidos_todos)
    total_paginas = max(1, math.ceil(total / por_pagina))
    if pagina > total_paginas:
        pagina = total_paginas

    inicio = (pagina - 1) * por_pagina
    pedidos = pedidos_todos[inicio : inicio + por_pagina]

    return render_template(
        "admin/pedidos/lista.html",
        pedidos=pedidos,
        estado_filtro=estado,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total,
        por_pagina=por_pagina,
    )


@admin_bp.route("/admin/pedidos/<numero>")
@rol_requerido("administrador")
def admin_pedido_detalle(numero):
    """Auditoría y detalle administrativo de un pedido con comprobación de stock."""
    pedido = Pedido.query.filter_by(numero=numero).first_or_404()
    return render_template("admin/pedidos/detalle.html", pedido=pedido)


@admin_bp.route("/admin/pedidos/<numero>/aprobar", methods=["POST"])
@rol_requerido("administrador")
def admin_pedido_aprobar(numero):
    """Ejecuta la aprobación atómica de un pedido descontando existencias físicas."""
    exito, mensaje = aprobar_pedido(numero, session["usuario_id"])
    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "error")
    return redirect(url_for("admin.admin_pedido_detalle", numero=numero))


@admin_bp.route("/admin/pedidos/<numero>/rechazar", methods=["POST"])
@rol_requerido("administrador")
def admin_pedido_rechazar(numero):
    """Ejecuta el rechazo de un pedido con registro obligatorio de motivo."""
    motivo = request.form.get("motivo", "").strip()
    exito, mensaje = rechazar_pedido(numero, session["usuario_id"], motivo)
    if exito:
        flash(mensaje, "info")
    else:
        flash(mensaje, "error")
    return redirect(url_for("admin.admin_pedido_detalle", numero=numero))
