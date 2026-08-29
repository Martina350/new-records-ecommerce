"""Pruebas de la base Flask incorporada en la Fase 2."""

import pytest

from app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


@pytest.mark.parametrize(
    "ruta",
    ["/", "/categorias", "/productos", "/contacto"],
)
def test_paginas_publicas_responden(client, ruta):
    respuesta = client.get(ruta)

    assert respuesta.status_code == 200
    assert b"New Records" in respuesta.data


def test_pagina_inexistente_usa_error_personalizado(client):
    respuesta = client.get("/ruta-que-no-existe")

    assert respuesta.status_code == 404
    assert b"Este lado del disco" in respuesta.data


def test_todas_las_plantillas_compilan():
    with app.app_context():
        for nombre in app.jinja_env.list_templates():
            app.jinja_env.get_template(nombre)

