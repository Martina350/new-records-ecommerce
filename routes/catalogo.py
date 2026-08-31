"""Rutas públicas de portada, categorías y catálogo."""

import math

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from auth import obtener_usuario_actual
from models import Categoria, Disco, db

catalogo_bp = Blueprint("catalogo", __name__)


@catalogo_bp.route("/")
def inicio():
    """Muestra la portada de New Records solo a usuarios no autenticados o redirige al contenido interno."""
    usuario = obtener_usuario_actual()
    if usuario is not None:
        if usuario.es_administrador():
            return redirect(url_for("admin.admin_dashboard"))
        return redirect(url_for("catalogo.productos"))
    return render_template("index.html")


@catalogo_bp.route("/categorias")
def categorias():
    """Muestra las categorías musicales activas desde PostgreSQL."""
    lista_categorias = (
        Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    )
    return render_template("categorias.html", categorias=lista_categorias)


@catalogo_bp.route("/productos")
def productos():
    """Muestra el catálogo dinámico de discos con filtros por categoría, búsqueda y paginación (8 por página)."""
    pagina = request.args.get("pagina", 1, type=int)
    if pagina < 1:
        pagina = 1
    por_pagina = 8

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

    consulta = consulta.order_by(Disco.album)
    total = consulta.count()
    total_paginas = max(1, math.ceil(total / por_pagina))
    if pagina > total_paginas:
        pagina = total_paginas

    lista_discos = consulta.offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    lista_categorias = (
        Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    )

    if (
        request.args.get("ajax") == "1"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        html_cards = render_template(
            "productos/_tarjetas_productos.html", discos=lista_discos
        )
        return jsonify(
            {
                "html": html_cards,
                "pagina": pagina,
                "total_paginas": total_paginas,
                "total": total,
                "por_pagina": por_pagina,
                "tiene_mas": pagina < total_paginas,
            }
        )

    return render_template(
        "productos.html",
        discos=lista_discos,
        categorias=lista_categorias,
        categoria_actual=categoria_actual,
        categoria_slug=categoria_slug or "todos",
        busqueda=busqueda,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total,
        por_pagina=por_pagina,
    )


@catalogo_bp.route("/productos/<codigo>")
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
