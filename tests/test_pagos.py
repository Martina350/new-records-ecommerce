"""Pruebas de métodos de pago y verificación por PIN — Fase 7."""

import os
from datetime import date, timedelta

from app import app
from models import MetodoPago, VerificacionTarjeta, ahora_utc, db
from payments import crear_verificacion, verificar_pin, DURACION_PIN_MINUTOS, MAX_INTENTOS_PIN

def pass_cliente():
    return os.getenv("CLIENTE_DEMO_PASSWORD", "5c45d1a0df71bcead793c6d654a14cbf")


def autenticar_cliente(client):
    return client.post(
        "/login",
        data={"email": "cliente@newrecords.local", "password": pass_cliente()},
        follow_redirects=True,
    )


def datos_tarjeta_demo():
    return {
        "marca": "VISA",
        "ultimos4": "1234",
        "titular": "Cliente Demo",
        "mes_vencimiento": 12,
        "anio_vencimiento": 2030,
    }


# ── Tests de acceso ──────────────────────────────────────────────────────────

def test_pagos_requiere_login(client):
    resp_metodos = client.get("/pago/metodos", follow_redirects=False)
    assert resp_metodos.status_code == 302
    assert "/login" in resp_metodos.headers["Location"]

    resp_agregar = client.get("/pago/agregar", follow_redirects=False)
    assert resp_agregar.status_code == 302
    assert "/login" in resp_agregar.headers["Location"]


def test_formulario_agregar_tarjeta(client):
    with client:
        autenticar_cliente(client)
        resp = client.get("/pago/agregar")
        assert resp.status_code == 200
        assert b"Registrar" in resp.data
        assert b"Tarjeta" in resp.data


# ── Tests del flujo de verificación ─────────────────────────────────────────

def test_agregar_crea_verificacion_pendiente(client):
    with client:
        autenticar_cliente(client)
        resp = client.post(
            "/pago/agregar",
            data={
                "titular": "Cliente Demo",
                "marca": "VISA",
                "numero": "4111111111111111",
                "mes_vencimiento": "12",
                "anio_vencimiento": "2030",
            },
            follow_redirects=False,
        )
        # Debe redirigir a la pantalla de verificación
        assert resp.status_code == 302
        assert "/pago/verificar/" in resp.headers["Location"]

        with app.app_context():
            verificacion = VerificacionTarjeta.query.filter_by(
                ultimos4="1111", marca="VISA"
            ).order_by(VerificacionTarjeta.id.desc()).first()
            assert verificacion is not None
            assert verificacion.verificada is False
            assert verificacion.intentos == 0


def test_agregar_rechaza_tarjeta_vencida(client):
    with client:
        autenticar_cliente(client)
        hoy = date.today()
        mes_vencido = 12 if hoy.month == 1 else hoy.month - 1
        anio_vencido = hoy.year - 1 if hoy.month == 1 else hoy.year

        with app.app_context():
            cantidad_inicial = VerificacionTarjeta.query.count()

        respuesta = client.post(
            "/pago/agregar",
            data={
                "titular": "Cliente Demo",
                "marca": "VISA",
                "numero": "4111111111111111",
                "mes_vencimiento": str(mes_vencido),
                "anio_vencimiento": str(anio_vencido),
            },
            follow_redirects=True,
        )

        assert respuesta.status_code == 200
        assert "vigente y válida" in respuesta.data.decode("utf-8")
        with app.app_context():
            assert VerificacionTarjeta.query.count() == cantidad_inicial


def test_pin_se_bloquea_exactamente_al_tercer_intento(client):
    with client:
        autenticar_cliente(client)
        with app.app_context():
            from models import Usuario

            usuario_id = Usuario.query.filter_by(
                email="cliente@newrecords.local"
            ).first().id
            verificacion, pin_correcto = crear_verificacion(
                usuario_id, datos_tarjeta_demo()
            )
            token = verificacion.token_verificacion
            pin_incorrecto = "000000" if pin_correcto != "000000" else "111111"

        for _ in range(MAX_INTENTOS_PIN):
            exito, _ = verificar_pin(token, pin_incorrecto)
            assert exito is False

        exito, mensaje = verificar_pin(token, pin_correcto)
        assert exito is False
        assert "máximo de intentos" in mensaje


def test_pin_incorrecto_incrementa_intentos(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            from models import Usuario
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            verificacion, _pin = crear_verificacion(usuario.id, datos_tarjeta_demo())
            token = verificacion.token_verificacion

        resp = client.post(
            f"/pago/verificar/{token}",
            data={"pin": "000000"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with app.app_context():
            v = VerificacionTarjeta.query.filter_by(token_verificacion=token).first()
            assert v.intentos == 1
            assert v.verificada is False


def test_pin_correcto_crea_metodo_pago(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            from models import Usuario
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            verificacion, pin_plano = crear_verificacion(usuario.id, datos_tarjeta_demo())
            token = verificacion.token_verificacion

        resp = client.post(
            f"/pago/verificar/{token}",
            data={"pin": pin_plano},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert "Tarjeta verificada" in resp.data.decode("utf-8")

        with app.app_context():
            v = VerificacionTarjeta.query.filter_by(token_verificacion=token).first()
            assert v.verificada is True
            metodo = MetodoPago.query.filter_by(token=v.token_tarjeta).first()
            assert metodo is not None
            assert metodo.activo is True


def test_pin_expirado_rechaza_verificacion(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            from models import Usuario
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            verificacion, pin_plano = crear_verificacion(usuario.id, datos_tarjeta_demo())
            token = verificacion.token_verificacion
            # Forzar expiración retroactiva
            verificacion.fecha_expiracion = ahora_utc() - timedelta(minutes=10)
            db.session.commit()

        exito, msg = verificar_pin(token, pin_plano)
        assert exito is False
        assert "expirado" in msg.lower()


def test_metodo_predeterminado(client):
    """Solo un método puede quedar como predeterminado a la vez."""
    with client:
        autenticar_cliente(client)

        with app.app_context():
            from models import Usuario
            from payments import establecer_predeterminado
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()

            # Crear y verificar dos métodos de pago
            v1, p1 = crear_verificacion(usuario.id, {**datos_tarjeta_demo(), "ultimos4": "1111"})
            verificar_pin(v1.token_verificacion, p1)
            v2, p2 = crear_verificacion(usuario.id, {**datos_tarjeta_demo(), "ultimos4": "2222"})
            verificar_pin(v2.token_verificacion, p2)

            metodo2 = MetodoPago.query.filter_by(
                usuario_id=usuario.id, ultimos4="2222", activo=True
            ).first()
            establecer_predeterminado(metodo2.id, usuario.id)

            predeterminados = MetodoPago.query.filter_by(
                usuario_id=usuario.id, activo=True, predeterminado=True
            ).count()
            assert predeterminados == 1


def test_desactivar_metodo_pago(client):
    with client:
        autenticar_cliente(client)

        with app.app_context():
            from models import Usuario
            from payments import desactivar_metodo_pago
            usuario = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            verificacion, pin_plano = crear_verificacion(
                usuario.id, {**datos_tarjeta_demo(), "ultimos4": "9999"}
            )
            verificar_pin(verificacion.token_verificacion, pin_plano)
            metodo = MetodoPago.query.filter_by(
                usuario_id=usuario.id, ultimos4="9999", activo=True
            ).first()
            assert metodo is not None

            resultado = desactivar_metodo_pago(metodo.id, usuario.id)
            assert resultado is True

            metodo_desactivado = db.session.get(MetodoPago, metodo.id)
            assert metodo_desactivado.activo is False
