"""Pruebas del sistema de autenticación, sesiones, roles y perfil de la Fase 4."""

import os
from flask import session

from app import app
from models import Usuario, db


def obtener_credenciales_demo():
    admin_pass = os.environ["ADMIN_PASSWORD"]
    cliente_pass = os.environ["CLIENTE_DEMO_PASSWORD"]
    return admin_pass, cliente_pass


def test_registro_usuario_exitoso(client):
    email_nuevo = "juan.perez@example.com"

    with app.app_context():
        existente = Usuario.query.filter_by(email=email_nuevo).first()
        if existente:
            db.session.delete(existente)
            db.session.commit()

    respuesta = client.post(
        "/registro",
        data={
            "nombre": "Juan Pérez",
            "email": email_nuevo,
            "password": "PasswordSeguro123!",
            "confirmar_password": "PasswordSeguro123!",
        },
        follow_redirects=True,
    )

    assert respuesta.status_code == 200
    assert b"Tu cuenta ha sido creada exitosamente" in respuesta.data

    with app.app_context():
        usuario = Usuario.query.filter_by(email=email_nuevo).first()
        assert usuario is not None
        assert usuario.nombre == "Juan Pérez"
        assert usuario.rol == "cliente"
        assert usuario.activo is True
        assert usuario.password_hash != "PasswordSeguro123!"
        assert usuario.check_password("PasswordSeguro123!")

        # Limpieza
        db.session.delete(usuario)
        db.session.commit()


def test_registro_rechaza_correo_duplicado(client):
    respuesta = client.post(
        "/registro",
        data={
            "nombre": "Cliente Duplicado",
            "email": "cliente@newrecords.local",
            "password": "PasswordSeguro123!",
            "confirmar_password": "PasswordSeguro123!",
        },
        follow_redirects=True,
    )

    assert respuesta.status_code == 200
    assert b"Ya existe una cuenta registrada con este correo" in respuesta.data


def test_registro_rechaza_password_corta_o_no_coincidente(client):
    # Contraseña corta (< 8 caracteres)
    resp1 = client.post(
        "/registro",
        data={
            "nombre": "Test Corto",
            "email": "corto@example.com",
            "password": "123",
            "confirmar_password": "123",
        },
        follow_redirects=True,
    )
    assert b"al menos 8 caracteres" in resp1.data

    # Contraseñas no coincidentes
    resp2 = client.post(
        "/registro",
        data={
            "nombre": "Test Disparejo",
            "email": "disparejo@example.com",
            "password": "Password123!",
            "confirmar_password": "OtraPassword456!",
        },
        follow_redirects=True,
    )
    assert b"Las contrase\xc3\xb1as no coinciden" in resp2.data


def test_registro_rechaza_correo_con_formato_invalido(client):
    respuesta = client.post(
        "/registro",
        data={
            "nombre": "Correo Inválido",
            "email": "correo-sin-arroba",
            "password": "PasswordSeguro123!",
            "confirmar_password": "PasswordSeguro123!",
        },
        follow_redirects=True,
    )

    assert respuesta.status_code == 200
    assert b"Introduce un correo electr\xc3\xb3nico v\xc3\xa1lido" in respuesta.data

    with app.app_context():
        assert Usuario.query.filter_by(email="correo-sin-arroba").first() is None


def test_login_exitoso_y_sesion(client):
    _, cliente_pass = obtener_credenciales_demo()
    with client:
        respuesta = client.post(
            "/login",
            data={
                "email": "cliente@newrecords.local",
                "password": cliente_pass,
            },
            follow_redirects=True,
        )

        assert respuesta.status_code == 200
        assert session.get("usuario_id") is not None
        assert session.get("usuario_rol") == "cliente"
        assert "usuario_email" not in session
        assert b"Bienvenido de nuevo" in respuesta.data


def test_login_rechaza_credenciales_invalidas_con_mensaje_generico(client):
    respuesta = client.post(
        "/login",
        data={
            "email": "noexiste@newrecords.local",
            "password": "ClaveCualquiera123!",
        },
        follow_redirects=True,
    )

    assert respuesta.status_code == 200
    assert b"Correo electr\xc3\xb3nico o contrase\xc3\xb1a incorrectos." in respuesta.data


def test_logout_limpia_la_sesion(client):
    _, cliente_pass = obtener_credenciales_demo()
    with client:
        client.post(
            "/login",
            data={
                "email": "cliente@newrecords.local",
                "password": cliente_pass,
            },
            follow_redirects=True,
        )
        assert session.get("usuario_id") is not None

        resp_logout = client.post("/logout", follow_redirects=True)
        assert resp_logout.status_code == 200
        assert session.get("usuario_id") is None
        assert session.get("usuario_rol") is None
        assert b"Has cerrado sesi\xc3\xb3n correctamente" in resp_logout.data


def test_login_requerido_protege_perfil(client):
    # Acceso sin sesión
    respuesta = client.get("/perfil", follow_redirects=False)
    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


def test_cliente_puede_ver_y_editar_perfil(client):
    _, cliente_pass = obtener_credenciales_demo()
    with client:
        client.post(
            "/login",
            data={
                "email": "cliente@newrecords.local",
                "password": cliente_pass,
            },
            follow_redirects=True,
        )

        resp_perfil = client.get("/perfil")
        assert resp_perfil.status_code == 200
        assert b"cliente@newrecords.local" in resp_perfil.data

        # Actualizar datos
        resp_actualizar = client.post(
            "/perfil",
            data={
                "nombre": "Cliente Demo Modificado",
                "telefono": "+59399887766",
                "ciudad": "Guayaquil",
                "direccion": "Av. 9 de Octubre 123",
            },
            follow_redirects=True,
        )
        assert resp_actualizar.status_code == 200
        assert b"Tu perfil ha sido actualizado correctamente" in resp_actualizar.data

        with app.app_context():
            u = Usuario.query.filter_by(email="cliente@newrecords.local").first()
            assert u.nombre == "Cliente Demo Modificado"
            assert u.telefono == "+59399887766"
            assert u.ciudad == "Guayaquil"
            assert u.direccion == "Av. 9 de Octubre 123"

            # Restaurar nombre demo
            u.nombre = "Cliente Demo"
            db.session.commit()


def test_rol_requerido_impide_acceso_de_cliente_a_admin(client):
    _, cliente_pass = obtener_credenciales_demo()
    with client:
        # Iniciar como cliente
        client.post(
            "/login",
            data={
                "email": "cliente@newrecords.local",
                "password": cliente_pass,
            },
            follow_redirects=True,
        )

        # Intentar acceder al dashboard admin
        resp_admin = client.get("/admin/dashboard")
        assert resp_admin.status_code == 403


def test_administrador_puede_acceder_a_dashboard(client):
    admin_pass, _ = obtener_credenciales_demo()
    with client:
        client.post(
            "/login",
            data={
                "email": "admin@newrecords.local",
                "password": admin_pass,
            },
            follow_redirects=True,
        )

        resp_admin = client.get("/admin/dashboard")
        assert resp_admin.status_code == 200
        assert b"Panel de" in resp_admin.data
        assert b"Administraci\xc3\xb3n" in resp_admin.data
