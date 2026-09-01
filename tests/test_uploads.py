"""Pruebas del flujo de carga y publicación de portadas."""

import base64
import os
import secrets
from io import BytesIO
from pathlib import Path

from app import app
from models import Categoria, Disco, db

PNG_UN_PIXEL = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _autenticar_admin(client):
    return client.post(
        "/login",
        data={
            "email": "admin@newrecords.local",
            "password": os.environ["ADMIN_PASSWORD"],
        },
        follow_redirects=True,
    )


def test_formulario_disco_envia_archivo_multipart(client):
    with client:
        _autenticar_admin(client)
        respuesta_disco = client.get("/admin/discos/nuevo")
        respuesta_categoria = client.get("/admin/categorias/nueva")
        formulario_disco = respuesta_disco.get_data(as_text=True)
        formulario_categoria = respuesta_categoria.get_data(as_text=True)

        assert respuesta_disco.status_code == 200
        assert respuesta_categoria.status_code == 200
        assert 'enctype="multipart/form-data"' in formulario_disco
        assert 'name="imagen_archivo"' in formulario_disco
        assert 'enctype="multipart/form-data"' in formulario_categoria
        assert 'name="imagen_archivo"' in formulario_categoria


def test_portada_subida_se_guarda_y_se_publica_en_catalogo(client):
    album = f"Portada pública {secrets.token_hex(5)}"
    ruta_archivo = None

    with client:
        _autenticar_admin(client)
        with app.app_context():
            categoria_id = Categoria.query.filter_by(activo=True).first().id

        try:
            respuesta = client.post(
                "/admin/discos/nuevo",
                data={
                    "formato": "CD",
                    "album": album,
                    "artista": "Artista de prueba",
                    "descripcion": "Disco creado para verificar su portada pública.",
                    "categoria_id": str(categoria_id),
                    "precio_base": "25.00",
                    "stock": "4",
                    "peso_kg": "0.200",
                    "costo_envio_por_kg": "2.00",
                    "imagen_archivo": (BytesIO(PNG_UN_PIXEL), "portada.png"),
                },
                content_type="multipart/form-data",
                follow_redirects=True,
            )

            assert respuesta.status_code == 200
            assert "creado exitosamente" in respuesta.get_data(as_text=True)

            with app.app_context():
                disco = Disco.query.filter_by(album=album).one()
                assert disco.imagen.startswith("img/uploads/productos/")
                ruta_imagen = disco.imagen
                ruta_archivo = Path(app.static_folder) / ruta_imagen
                assert ruta_archivo.is_file()

            respuesta_imagen = client.get(f"/static/{ruta_imagen}")
            assert respuesta_imagen.status_code == 200
            assert respuesta_imagen.data == PNG_UN_PIXEL
            respuesta_imagen.close()

            catalogo = client.get("/productos", query_string={"q": album})
            contenido_catalogo = catalogo.get_data(as_text=True)
            assert catalogo.status_code == 200
            assert f"/static/{ruta_imagen}" in contenido_catalogo
        finally:
            with app.app_context():
                disco = Disco.query.filter_by(album=album).first()
                if disco is not None:
                    db.session.delete(disco)
                    db.session.commit()
            if ruta_archivo is not None:
                ruta_archivo.unlink(missing_ok=True)
