"""Pruebas del catálogo dinámico, filtros, detalle de discos y recomendaciones de la Fase 5."""

from decimal import Decimal
from pathlib import Path

from app import app
from models import CD, Categoria, Disco, Vinilo, db


def test_categorias_dinamicas_responden(client):
    respuesta = client.get("/categorias")
    assert respuesta.status_code == 200
    assert b"Rock" in respuesta.data
    assert b"Pop" in respuesta.data
    assert b"Reggaeton" in respuesta.data


def test_menu_global_lista_generos_desde_postgresql(client):
    respuesta = client.get("/productos")
    assert respuesta.status_code == 200
    assert b"filtroCategoria" in respuesta.data
    assert b"rock" in respuesta.data
    assert b"pop" in respuesta.data
    assert b"reggaeton" in respuesta.data


def test_catalogo_todos_los_productos(client):
    """Verifica la paginación del catálogo con 8 álbumes por página."""
    resp_pag1 = client.get("/productos")
    assert resp_pag1.status_code == 200
    assert b"Deb\xc3\xad Tirar M\xc3\xa1s Fotos" in resp_pag1.data
    assert b"Future Nostalgia" in resp_pag1.data

    resp_pag2 = client.get("/productos?pagina=2")
    assert resp_pag2.status_code == 200
    assert b"The Dark Side of the Moon" in resp_pag2.data
    assert b"Hit Me Hard and Soft" in resp_pag2.data


def test_catalogo_carga_mas_ajax(client):
    """Verifica que el endpoint AJAX para móvil retorne JSON con HTML de tarjetas."""
    respuesta = client.get("/productos?pagina=2&ajax=1")
    assert respuesta.status_code == 200
    data = respuesta.get_json()
    assert data is not None
    assert "html" in data
    assert data["pagina"] == 2
    assert data["total_paginas"] >= 2
    assert "The Dark Side of the Moon" in data["html"]
    assert "Hit Me Hard and Soft" in data["html"]




def test_filtro_productos_por_categoria(client):
    # Filtrar por Rock
    resp_rock = client.get("/productos?categoria=rock")
    assert resp_rock.status_code == 200
    assert b"The Dark Side of the Moon" in resp_rock.data
    assert b"Nevermind" in resp_rock.data
    assert b"Abbey Road" in resp_rock.data
    assert b"Deb\xc3\xad Tirar M\xc3\xa1s Fotos" not in resp_rock.data

    # Filtrar por Pop
    resp_pop = client.get("/productos?categoria=pop")
    assert resp_pop.status_code == 200
    assert b"Future Nostalgia" in resp_pop.data
    assert b"After Hours" in resp_pop.data
    assert b"Pink Floyd" not in resp_pop.data

    # Filtrar por Reggaeton
    resp_reggaeton = client.get("/productos?categoria=reggaeton")
    assert resp_reggaeton.status_code == 200
    assert b"Deb\xc3\xad Tirar M\xc3\xa1s Fotos" in resp_reggaeton.data
    assert b"Atrevido" in resp_reggaeton.data
    assert b"FERXXOCALIPSIS" in resp_reggaeton.data
    assert b"Dua Lipa" not in resp_reggaeton.data


def test_javascript_no_oculta_resultados_filtrados_por_flask():
    """El catálogo se filtra en PostgreSQL y no vuelve a ocultarse en el navegador."""
    ruta_script = Path(__file__).resolve().parent.parent / "static" / "js" / "script.js"
    contenido = ruta_script.read_text(encoding="utf-8")

    assert "card.style.display" not in contenido
    assert "getAttribute('data-categoria')" not in contenido


def test_busqueda_productos_por_texto(client):
    respuesta = client.get("/productos?q=Floyd")
    assert respuesta.status_code == 200
    assert b"The Dark Side of the Moon" in respuesta.data
    assert b"Dua Lipa" not in respuesta.data


def test_detalle_producto_cd(client):
    # NR-POP-001 es Dua Lipa - Future Nostalgia (CD)
    # Precio base: 29.99, peso: 0.120, costo_envio: 2.50 -> Envio: 0.30 -> Total: 30.29
    respuesta = client.get("/productos/NR-POP-001")
    assert respuesta.status_code == 200
    assert b"Future Nostalgia" in respuesta.data
    assert b"Dua Lipa" in respuesta.data
    assert b"Formato CD" in respuesta.data
    assert b"29.99" in respuesta.data
    assert b"30.29" in respuesta.data
    assert b"Discos recomendados" in respuesta.data


def test_detalle_producto_vinilo(client):
    # NR-REG-001 es Bad Bunny - DTMF (VINILO)
    # Precio base: 35.00, peso: 0.450, costo_envio: 2.50 (1.125), embalaje: 1.50 -> Total: 37.625 -> 37.62 / 37.63
    respuesta = client.get("/productos/NR-REG-001")
    assert respuesta.status_code == 200
    assert b"Bad Bunny" in respuesta.data
    assert b"Formato VINILO" in respuesta.data
    assert b"35.00" in respuesta.data
    assert b"Embalaje protector para vinilo" in respuesta.data
    assert b"37.62" in respuesta.data or b"37.63" in respuesta.data


def test_detalle_producto_inexistente_retorna_404(client):
    respuesta = client.get("/productos/NR-CODIGO-INVENTADO")
    assert respuesta.status_code == 404
    assert b"Este lado del disco" in respuesta.data


def test_disco_inactivo_no_se_muestra_en_catalogo_ni_detalle(client):
    codigo_inactivo = f"NR-INACT-{Decimal('100')}"
    with app.app_context():
        # Limpieza previa por si acaso
        existente = Disco.query.filter_by(codigo="NR-TEST-INACTIVO").first()
        if existente:
            db.session.delete(existente)
            db.session.commit()

        categoria = Categoria.query.filter_by(slug="rock").first()
        disco_inactivo = CD(
            categoria=categoria,
            codigo="NR-TEST-INACTIVO",
            album="Album Oculto",
            artista="Banda Secreta",
            descripcion="Disco de prueba inactivo",
            precio_base=Decimal("15.00"),
            stock=5,
            peso_kg=Decimal("0.100"),
            costo_envio_por_kg=Decimal("2.00"),
            costo_embalaje=Decimal("0.00"),
            activo=False,
        )
        db.session.add(disco_inactivo)
        db.session.commit()

    try:
        # En catálogo general no debe aparecer
        resp_cat = client.get("/productos")
        assert b"Album Oculto" not in resp_cat.data

        # Al intentar ver su detalle debe dar 404
        resp_det = client.get("/productos/NR-TEST-INACTIVO")
        assert resp_det.status_code == 404
    finally:
        # Limpieza garantizada
        with app.app_context():
            d = Disco.query.filter_by(codigo="NR-TEST-INACTIVO").first()
            if d:
                db.session.delete(d)
                db.session.commit()
