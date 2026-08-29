"""Pruebas del sistema de carrito de compras y preparación de checkout de la Fase 6."""

import os
import pytest
from flask import session

from app import app
from models import Disco, db


@pytest.fixture()
def client():
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    return app.test_client()


def obtener_cliente_pass():
    return os.getenv("CLIENTE_DEMO_PASSWORD", "5c45d1a0df71bcead793c6d654a14cbf")


def autenticar_cliente(client):
    return client.post(
        "/login",
        data={
            "email": "cliente@newrecords.local",
            "password": obtener_cliente_pass(),
        },
        follow_redirects=True,
    )


def test_carrito_requiere_login(client):
    resp_get = client.get("/carrito", follow_redirects=False)
    assert resp_get.status_code == 302
    assert "/login" in resp_get.headers["Location"]

    resp_post = client.post("/carrito/agregar/1", follow_redirects=False)
    assert resp_post.status_code == 302
    assert "/login" in resp_post.headers["Location"]


def test_agregar_disco_al_carrito(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            disco = Disco.query.filter_by(codigo="NR-POP-001").first()
            disco_id = disco.id

        respuesta = client.post(
            f"/carrito/agregar/{disco_id}",
            data={"cantidad": 1},
            follow_redirects=True,
        )

        assert respuesta.status_code == 200
        assert session.get("carrito") is not None
        assert session["carrito"].get(str(disco_id)) == 1
        assert b"Future Nostalgia" in respuesta.data


def test_incrementar_cantidad_mismo_disco(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            disco = Disco.query.filter_by(codigo="NR-POP-001").first()
            disco_id = disco.id

        client.post(f"/carrito/agregar/{disco_id}", data={"cantidad": 1})
        client.post(f"/carrito/agregar/{disco_id}", data={"cantidad": 2})

        assert session["carrito"].get(str(disco_id)) == 3


def test_actualizar_y_eliminar_item_carrito(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            disco = Disco.query.filter_by(codigo="NR-REG-001").first()
            disco_id = disco.id

        # Agregar
        client.post(f"/carrito/agregar/{disco_id}", data={"cantidad": 1})
        assert session["carrito"].get(str(disco_id)) == 1

        # Actualizar cantidad a 4
        client.post(f"/carrito/actualizar/{disco_id}", data={"cantidad": 4})
        assert session["carrito"].get(str(disco_id)) == 4

        # Eliminar item
        client.post(f"/carrito/eliminar/{disco_id}", follow_redirects=True)
        assert str(disco_id) not in session.get("carrito", {})


def test_no_permite_cantidad_mayor_al_stock(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            disco = Disco.query.filter_by(codigo="NR-ROC-004").first()  # Stock: 7
            disco_id = disco.id
            stock_maximo = disco.stock

        # Intentar agregar 100 unidades (superior al stock de 7)
        client.post(f"/carrito/agregar/{disco_id}", data={"cantidad": 100})
        assert session["carrito"].get(str(disco_id)) == stock_maximo


def test_calculo_polimorfico_total_carrito(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            cd = Disco.query.filter_by(codigo="NR-POP-001").first()  # Total: 30.29
            vinilo = Disco.query.filter_by(codigo="NR-REG-001").first()  # Total: 37.625

            cd_id = cd.id
            vinilo_id = vinilo.id
            total_esperado = cd.precio_final() + vinilo.precio_final()

        # Vaciar carrito previo
        client.post("/carrito/vaciar")

        client.post(f"/carrito/agregar/{cd_id}", data={"cantidad": 1})
        client.post(f"/carrito/agregar/{vinilo_id}", data={"cantidad": 1})

        respuesta = client.get("/carrito")
        assert respuesta.status_code == 200

        monto_str = f"{total_esperado:.2f}"
        assert monto_str.encode("utf-8") in respuesta.data


def test_checkout_resumen_valida_carrito_vacio(client):
    with client:
        autenticar_cliente(client)
        client.post("/carrito/vaciar")

        respuesta = client.get("/checkout/resumen", follow_redirects=True)
        assert respuesta.status_code == 200
        assert b"Tu carrito est\xc3\xa1 vac\xc3\xado" in respuesta.data


def test_checkout_resumen_muestra_items_y_datos_envio(client):
    with client:
        autenticar_cliente(client)
        with app.app_context():
            disco = Disco.query.filter_by(codigo="NR-ROC-001").first()
            disco_id = disco.id

        client.post(f"/carrito/agregar/{disco_id}", data={"cantidad": 1})

        respuesta = client.get("/checkout/resumen")
        assert respuesta.status_code == 200
        assert b"Resumen de" in respuesta.data
        assert b"Checkout" in respuesta.data
        assert b"The Dark Side of the Moon" in respuesta.data
        assert b"Cliente Demo" in respuesta.data
